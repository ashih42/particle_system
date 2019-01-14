from OpenGL.GL import *

from exceptions import ParticleSystemException
from file_to_string import file_to_string

class Shader:

	def __init__(self, vs_filename, fs_filename):
		# compile shaders
		vertex_shader = self.__compile_shader(vs_filename, GL_VERTEX_SHADER)
		fragment_shader = self.__compile_shader(fs_filename, GL_FRAGMENT_SHADER)

		# link shader program
		self.__ID = self.__link_shader(vertex_shader, fragment_shader)
		glUseProgram(self.__ID)
		
		# don't need these anymore
		glDeleteShader(vertex_shader)
		glDeleteShader(fragment_shader)

	def __compile_shader(self, shader_filename, shader_type):
		shader_source = file_to_string(shader_filename)
		shader = glCreateShader(shader_type)
		glShaderSource(shader, shader_source)
		glCompileShader(shader)

		if not glGetShaderiv(shader, GL_COMPILE_STATUS):
			info_log = glGetShaderInfoLog(shader)
			raise ParticleSystemException('ERROR: SHADER COMPILATION FAILED: ' + \
				shader_filename + '\n' + info_log.decode())

		return shader

	def __link_shader(self, vertex_shader, fragment_shader):
		shader_program = glCreateProgram()
		glAttachShader(shader_program, vertex_shader)
		glAttachShader(shader_program, fragment_shader)
		glLinkProgram(shader_program)

		if not glGetProgramiv(shader_program, GL_LINK_STATUS):
			info_log = glGetProgramInfoLog(shader_program)
			raise ParticleSystemException('ERROR: SHADER LINKING FAILED\n' + info_log.decode())

		return shader_program

	def set_matrix(self, name, value):
		loc = glGetUniformLocation(self.__ID, name)
		glUniformMatrix4fv(loc, 1, GL_TRUE, value)	# Transpose=TRUE, important!

	def set_float(self, name, value):
		loc = glGetUniformLocation(self.__ID, name)
		glUniform1f(loc, value)

	def set_bool(self, name, value):
		loc = glGetUniformLocation(self.__ID, name)
		glUniform1i(loc, int(value))
