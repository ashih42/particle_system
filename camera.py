import numpy as np

def normalize(vector):
	return vector / np.linalg.norm(vector)

class Camera:

	__PITCH_LOWER_LIMIT = -89.0
	__PITCH_UPPER_LIMIT = 89.0

	def __init__(self):
		self.position = np.array([0.0, 0.0, 5.0])
		self.__front = np.array([0.0, 0.0, -1.0])
		self.__up = np.array([0.0, 1.0, 0.0])

		self.__pitch = 0.0		# degrees
		self.__yaw = -90.0		# degrees

	def update_yaw_pitch(self, yaw_offset, pitch_offset):
		self.__yaw += yaw_offset
		self.__pitch += pitch_offset

		if self.__pitch < Camera.__PITCH_LOWER_LIMIT:
			self.__pitch = Camera.__PITCH_LOWER_LIMIT
		elif self.__pitch > Camera.__PITCH_UPPER_LIMIT:
			self.__pitch = Camera.__PITCH_UPPER_LIMIT

		self.__front[0] = np.cos(np.radians(self.__yaw)) * np.cos(np.radians(self.__pitch))
		self.__front[1] = np.sin(np.radians(self.__pitch))
		self.__front[2] = np.sin(np.radians(self.__yaw)) * np.cos(np.radians(self.__pitch))
		self.__front = normalize(self.__front)

	def get_view_matrix(self):
		self.__update_local_axes()
		return np.array([
				[*self.local_right, 0.0],
				[*self.local_up, 0.0],
				[*self.local_front, 0.0],
				[0.0, 0.0, 0.0, 1.0]]) @ \
			np.array([
				[1.0, 0.0, 0.0, -self.position[0]],
				[0.0, 1.0, 0.0, -self.position[1]],
				[0.0, 0.0, 1.0, -self.position[2]],
				[0.0, 0.0, 0.0, 1.0]])

		return look_at(self.position, self.position + self.__front, self.__up)

	def get_rotation_matrix(self):
		self.__update_local_axes()
		return np.array([
				[*self.local_right, 0.0],
				[*self.local_up, 0.0],
				[*self.local_front, 0.0],
				[0.0, 0.0, 0.0, 1.0]])

	def __update_local_axes(self):
		target = self.position + self.__front
		self.local_front = normalize(self.position - target)
		self.local_right = normalize(np.cross(self.__up, self.local_front))
		self.local_up = np.cross(self.local_front, self.local_right)
