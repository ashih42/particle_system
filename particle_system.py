import glfw
from OpenGL.GL import *
from OpenGL.raw.GL import _types
from PIL import Image

import pyopencl as cl
from pyopencl.tools import get_gl_sharing_context_properties

import numpy as np
from os import path
import sys
from colorama import Fore, Back, Style

from shader import Shader
from camera import Camera
from exceptions import ParticleSystemException
from file_to_string import file_to_string

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

ASPECT_RATIO = SCREEN_WIDTH / SCREEN_HEIGHT
FOV_DEGREES = 54

MOUSE_SENSITIVITY = 0.05

TEXTURE_FILENAME = 'textures/doge.png'

VERTEX_SHADER_FILENAME = 'shaders/vertex_shader.glsl'
FRAGMENT_SHADER_FILENAME = 'shaders/fragment_shader.glsl'

KERNEL_FILENAME = 'kernels/kernel.cl'

COLOR_PROFILES = (
	'Confetti',
	'Monochrome',
	'Red and White',
	'Cyan Magenta Yellow',
	'Rainbow Dash',
	)

PARTICLE_MODES = (
	'Stationary',
	'Falling Down',
	'Gravity Fountain',
	'Radial Explosion',
	'Chaos Nova',
	'Vortex Attractor',
	)


# check for key press events
def key_callback(window, key, scancode, action, mods):
	ps = glfw.get_window_user_pointer(window)

	if action == glfw.PRESS:
		if key == glfw.KEY_ESCAPE:
			glfw.set_window_should_close(window, True)
		elif key == glfw.KEY_P:
			ps.toggle_projection_mode()
		elif key == glfw.KEY_Z:
			ps.toggle_spawn_location()
		elif key == glfw.KEY_L:
			ps.toggle_lifetime()
		elif key == glfw.KEY_G:
			ps.toggle_gravity()
		elif key == glfw.KEY_T:
			ps.toggle_texture()
		elif key == glfw.KEY_X:
			ps.toggle_shrinking()
		elif key == glfw.KEY_TAB:
			ps.toggle_particle_mode()
		elif key == glfw.KEY_C:
			ps.toggle_color_profile()

def set_generator_position(ps, mouse_ndc_x, mouse_ndc_y):
	mouse_camera_space = np.array([mouse_ndc_x / (2), mouse_ndc_y / (2), -1.0])
	mouse_camera_space = np.linalg.inv(ps.camera.get_rotation_matrix()) @ np.array([*mouse_camera_space, 1.0])
	
	RAY_DIRECTION = mouse_camera_space[:3]
	RAY_DIRECTION = RAY_DIRECTION / np.linalg.norm(RAY_DIRECTION)

	DISTANCE_CAMERA_GENERATOR = np.linalg.norm(ps.generator_position[:3] - ps.camera.position)

	new_position = ps.camera.position + DISTANCE_CAMERA_GENERATOR * RAY_DIRECTION
	ps.generator_position[0] = new_position[0]
	ps.generator_position[1] = new_position[1]
	ps.generator_position[2] = new_position[2]

def mouse_callback(window, pos_x, pos_y):
	ps = glfw.get_window_user_pointer(window)

	if ps.last_mouse_pos_x is None:
		ps.last_mouse_pos_x = pos_x
		ps.last_mouse_pos_y = pos_y
	else:
		x_offset = (pos_x - ps.last_mouse_pos_x)
		y_offset = (ps.last_mouse_pos_y - pos_y)
		ps.last_mouse_pos_x = pos_x
		ps.last_mouse_pos_y = pos_y

		# Send shader the mouse (x, y) in NDC space
		mouse_ndc_x = pos_x / SCREEN_WIDTH * 2 - 1
		mouse_ndc_y = -(pos_y / SCREEN_HEIGHT * 2 - 1)

		ps.shader.set_float('mouse_x', mouse_ndc_x)
		ps.shader.set_float('mouse_y', mouse_ndc_y)

		# Set the particle generator position
		if glfw.get_key(window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS and 0 < pos_x < SCREEN_WIDTH and 0 < pos_y < SCREEN_HEIGHT:
			set_generator_position(ps, mouse_ndc_x, mouse_ndc_y)

		# Rotate camera
		if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
			ps.camera.update_yaw_pitch(x_offset * MOUSE_SENSITIVITY, y_offset * MOUSE_SENSITIVITY)

# https://www.scratchapixel.com/lessons/3d-basic-rendering/perspective-and-orthographic-projection-matrix/orthographic-projection-matrix
def get_orthographic_projection(near=0.1, far=100.0):
	left = -3.0
	right = 3.0
	bottom = -3.0
	top = 3.0
	return np.array([
		[2 / (right - left), 0.0, 0.0, -(right + left) / (right - left)],
		[0.0, 2 / (top - bottom), 0.0, -(top + bottom) / (top - bottom)],
		[0.0, 0.0, -2 / (far - near), -(far + near) / (far - near)],
		[0.0, 0.0, 0.0, 1.0]
		], dtype=np.float32)

# ¯\_(ツ)_/¯
def get_perspective_projection(fov_degrees, aspect_ratio, near=0.1, far=100.0):
	fov_radians = np.radians(fov_degrees)
	return np.array([
		[1 / (aspect_ratio * np.tan(fov_radians / 2)), 0.0, 0.0, 0.0],
		[0.0, 1 / np.tan(fov_radians / 2), 0.0, 0.0],
		[0.0, 0.0, -(far + near) / (far - near), -2 * far * near / (far - near)],
		[0.0, 0.0, -1.0, 0.0]
		], dtype=np.float32)



class ParticleSystem:

	def __init__(self, n_particles):
		self.n_particles = n_particles

		self.generator_position = np.array( [0.0, 0.0, 0.0, 1.0], dtype=np.float32)

		self.is_perspective = True
		self.spawn_in_cube = False
		self.is_decaying = True
		self.is_gravity_on = False
		self.is_texture = False
		self.is_shrinking = False
		self.particle_mode_id = 0
		self.color_profile_id = 0
		self.point_size = 1

		self.delta_time = 0.0
		self.last_frame = 0.0

		self.last_mouse_pos_x = None	# will be initialized in mouse_callback
		self.last_mouse_pos_y = None

		self.__init_window()
		self.__init_texture()
		self.__init_gl_objects()
		self.__init_cl_stuff()

		self.shader = Shader(VERTEX_SHADER_FILENAME, FRAGMENT_SHADER_FILENAME)
		self.camera = Camera()

		self.PERSPECTIVE_PROJECTION = get_perspective_projection(FOV_DEGREES, ASPECT_RATIO)
		self.ORTHOGRAPHIC_PROJECTION = get_orthographic_projection()

		self.shader.set_matrix('projection', self.__get_projection_matrix())
		self.shader.set_matrix('model', np.identity(4))
		self.shader.set_bool('is_texture', self.is_texture)

		# glEnable(GL_DEPTH_TEST)		# THIS REALLY SLOWS DOWN FRAME RATE
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
		self.shader.set_float('point_size', float(self.point_size))
		self.shader.set_bool('is_shrinking', self.is_shrinking)
		glClearColor(0.0, 0.0, 0.0, 0.0)

	def loop(self):
		# Run __kernel init() once
		cl.enqueue_acquire_gl_objects(self.queue, self.gl_buffers)
		self.kernel.init(self.queue, (self.n_particles,), None,
			*self.gl_buffers,
			self.velocity_buffer,
			self.seed_buffer,
			self.generator_position,
			np.int32(self.spawn_in_cube),
			np.int32(self.particle_mode_id),
			np.int32(self.color_profile_id))
		cl.enqueue_release_gl_objects(self.queue, self.gl_buffers)
		self.queue.finish()
		glFlush()

		while not glfw.window_should_close(self.window):
			self.__update_frame_counter()
			self.__process_key_input()
			self.shader.set_matrix('view', self.camera.get_view_matrix())

			# Run __kernel update() on each frame
			cl.enqueue_acquire_gl_objects(self.queue, self.gl_buffers)
			self.kernel.update(self.queue, (self.n_particles,), None,
				*self.gl_buffers,
				self.velocity_buffer,
				self.seed_buffer,
				self.generator_position,
				np.int32(self.spawn_in_cube),
				np.int32(self.is_decaying),
				np.int32(self.is_gravity_on),
				np.int32(self.particle_mode_id),
				np.int32(self.color_profile_id))
			cl.enqueue_release_gl_objects(self.queue, self.gl_buffers)
			self.queue.finish()
			glFlush()

			# Render
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glDrawArrays(GL_POINTS, 0, self.n_particles)
			glfw.swap_buffers(self.window)
			glfw.poll_events()

	def toggle_projection_mode(self):
		self.is_perspective = not self.is_perspective
		self.shader.set_matrix('projection', self.__get_projection_matrix())
		print(Style.BRIGHT + 'Projection: \t' + Style.RESET_ALL, ('Perspective' if self.is_perspective else 'Orthographic'))

	def toggle_spawn_location(self):
		self.spawn_in_cube = not self.spawn_in_cube
		print(Style.BRIGHT + 'Spawn in: \t' + Style.RESET_ALL, ('Cube' if self.spawn_in_cube else 'Sphere'))

	def toggle_lifetime(self):
		self.is_decaying = not self.is_decaying
		print(Style.BRIGHT + 'Life decay: \t' + Style.RESET_ALL, ('On' if self.is_decaying else 'Off'))

	def toggle_gravity(self):
		self.is_gravity_on = not self.is_gravity_on
		print(Style.BRIGHT + 'Gravity mod: \t' + Style.RESET_ALL, ('On' if self.is_gravity_on else 'Off'))

	def toggle_texture(self):
		self.is_texture = not self.is_texture
		self.shader.set_bool('is_texture', self.is_texture)
		print(Style.BRIGHT + 'Texture: \t' + Style.RESET_ALL, ('Doge' if self.is_texture else 'Not doge'))

	def toggle_shrinking(self):
		self.is_shrinking = not self.is_shrinking
		self.shader.set_bool('is_shrinking', self.is_shrinking)
		print(Style.BRIGHT + 'Shrinking: \t' + Style.RESET_ALL, ('On' if self.is_shrinking else 'Off'))
		
	def toggle_particle_mode(self):
		self.particle_mode_id = (self.particle_mode_id + 1) % len(PARTICLE_MODES)
		print(Style.BRIGHT + Fore.BLUE + 'Particle Mode: \t' + Fore.RESET + Style.RESET_ALL, PARTICLE_MODES[self.particle_mode_id])

	def toggle_color_profile(self):
		self.color_profile_id = (self.color_profile_id + 1) % len(COLOR_PROFILES)
		print(Style.BRIGHT + Fore.GREEN + 'Color Profile: \t' + Fore.RESET + Style.RESET_ALL, COLOR_PROFILES[self.color_profile_id])

		# Run __kernel change_color()
		cl.enqueue_acquire_gl_objects(self.queue, self.gl_buffers)
		self.kernel.change_color(self.queue, (self.n_particles,), None,
			self.color_buffer,
			self.seed_buffer,
			np.int32(self.color_profile_id))
		cl.enqueue_release_gl_objects(self.queue, self.gl_buffers)
		self.queue.finish()
		glFlush()

	def __adjust_point_size(self, offset):
		self.point_size += offset
		if self.point_size < 1:
			self.point_size = 1
		self.shader.set_float('point_size', float(self.point_size))

	def __get_projection_matrix(self):
		return self.PERSPECTIVE_PROJECTION if self.is_perspective else self.ORTHOGRAPHIC_PROJECTION

	def __update_frame_counter(self):
		current_frame = glfw.get_time()
		self.delta_time = current_frame - self.last_frame
		self.last_frame = current_frame

		fps = 1.0 / self.delta_time
		glfw.set_window_title(self.window, 'Particle System (FPS: %.0f)' % fps)
		
	# Check key states for held key inputs
	def __process_key_input(self):
		CAMERA_SPEED = 2.5 * self.delta_time

		# Move camera
		if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS:
			self.camera.position -= CAMERA_SPEED * self.camera.local_front
		if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
			self.camera.position += CAMERA_SPEED * self.camera.local_front
		if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS:
			self.camera.position -= CAMERA_SPEED * self.camera.local_right
		if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
			self.camera.position += CAMERA_SPEED * self.camera.local_right

		# Rendering options
		if glfw.get_key(self.window, glfw.KEY_PAGE_UP) == glfw.PRESS:
			self.__adjust_point_size(1)
		if glfw.get_key(self.window, glfw.KEY_PAGE_DOWN) == glfw.PRESS:
			self.__adjust_point_size(-1)

		# Move generator position
		if glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS:
			self.generator_position -= np.array([*self.camera.local_right, 0.0]) * 0.02
		if glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS:
			self.generator_position += np.array([*self.camera.local_right, 0.0]) * 0.02
		if glfw.get_key(self.window, glfw.KEY_DOWN) == glfw.PRESS:
			self.generator_position -= np.array([*self.camera.local_up, 0.0]) * 0.02
		if glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS:
			self.generator_position += np.array([*self.camera.local_up, 0.0]) * 0.02
		if glfw.get_key(self.window, glfw.KEY_HOME) == glfw.PRESS:
			self.generator_position -= np.array([*self.camera.local_front, 0.0]) * 0.02
		if glfw.get_key(self.window, glfw.KEY_END) == glfw.PRESS:
			self.generator_position += np.array([*self.camera.local_front, 0.0]) * 0.02

	def __init_window(self):
		if not glfw.init():
			raise ParticleSystemException('glfw.init() failed')

		glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
		glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
		glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
		glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)			# needed on Mac OS X

		glfw.window_hint(glfw.RESIZABLE, False)

		self.window = glfw.create_window(SCREEN_WIDTH, SCREEN_HEIGHT, 'Particle System', None, None)
		if self.window is None:
			raise ParticlSystemException('glfw.create_window() failed')

		glfw.set_window_pos(self.window, 0, 0)
		glfw.make_context_current(self.window)
		glfw.swap_interval(0)										# gotta go fast

		glfw.set_window_user_pointer(self.window, self)
		glfw.set_key_callback(self.window, key_callback)
		glfw.set_cursor_pos_callback(self.window, mouse_callback)

	def __init_texture(self):
		base_path = path.dirname(__file__)
		file_path = path.join(base_path, TEXTURE_FILENAME)
		im = Image.open(file_path)
		im_data = np.fromstring(im.tobytes(), np.uint8)

		texture_loc = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture_loc)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, im.size[0], im.size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, im_data);

	def __init_gl_objects(self):
		# One VAO to RULE THEM ALL
		self.vao = glGenVertexArrays(1)
		glBindVertexArray(self.vao)

		# Position VBO
		self.position_vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.position_vbo)
		glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(_types.GLfloat) * 4 * self.n_particles, None, GL_DYNAMIC_DRAW)
		glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * ctypes.sizeof(_types.GLfloat), None)
		glEnableVertexAttribArray(0)

		# Color VBO
		self.color_vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.color_vbo)
		glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(_types.GLfloat) * 4 * self.n_particles, None, GL_DYNAMIC_DRAW)
		glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 4 * ctypes.sizeof(_types.GLfloat), None)
		glEnableVertexAttribArray(1)

		# Lifetime VBO
		self.lifetime_vbo = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.lifetime_vbo)
		glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(_types.GLfloat) * 1 * self.n_particles, None, GL_DYNAMIC_DRAW)
		glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 1 * ctypes.sizeof(_types.GLfloat), None)
		glEnableVertexAttribArray(2)

	def __init_cl_stuff(self):
		# Figure out platform and device
		platform = cl.get_platforms()[0]
		if sys.platform == "darwin":
			self.context = cl.Context(properties=get_gl_sharing_context_properties(), devices=[])
		else:
			# Some OSs prefer clCreateContextFromType, some prefer clCreateContext. Try both.
			try:
				self.context = cl.Context(properties=[(cl.context_properties.PLATFORM, platform)] + get_gl_sharing_context_properties())
			except:
				self.context = cl.Context(properties=[(cl.context_properties.PLATFORM, platform)] + get_gl_sharing_context_properties(),
					devices = [platform.get_devices()[0]])

		print(Style.BRIGHT + 'DEVICE: ' + Style.RESET_ALL, self.context.devices[0])
		print(Style.BRIGHT + 'VERSION:' + Style.RESET_ALL, self.context.devices[0].get_info(cl.device_info.VERSION))

		# Make OpenCL buffers, one for each OpenGL VBO
		self.position_buffer = cl.GLBuffer(self.context, cl.mem_flags.READ_WRITE, int(self.position_vbo))
		self.color_buffer = cl.GLBuffer(self.context, cl.mem_flags.READ_WRITE, int(self.color_vbo))
		self.lifetime_buffer = cl.GLBuffer(self.context, cl.mem_flags.READ_WRITE, int(self.lifetime_vbo))
		self.gl_buffers = ( self.position_buffer, self.color_buffer, self.lifetime_buffer )

		# Make other OpenCL buffers
		self.seed_buffer = cl.Buffer(self.context, cl.mem_flags.READ_WRITE, self.n_particles * 8)			# buffer of ulong
		self.velocity_buffer = cl.Buffer(self.context, cl.mem_flags.READ_WRITE, self.n_particles * 4 * 4)	# buffer of float4

		# Compile kernel program
		try:
			program_src = file_to_string(KERNEL_FILENAME)
			self.kernel = cl.Program(self.context, program_src).build()
		except cl.RuntimeError as e:
			raise ParticleSystemException('Error compiling ' + KERNEL_FILENAME + '\n' + str(e))

		# Will need a command queue to run kernel
		self.queue = cl.CommandQueue(self.context)

