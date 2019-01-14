import sys

from particle_system import ParticleSystem
from exceptions import ParticleSystemException
from colorama import Fore, Back, Style

def terminate_with_usage():
	print(Style.BRIGHT + 'usage: ' + Style.RESET_ALL + 'python3 ' + Fore.BLUE + 'main.py ' + Fore.RESET +
		'n_particles \t\t (n_particles > 0)')
	print(Style.BRIGHT + '\n[CONTROLS]' + Style.RESET_ALL)
	print(Fore.BLUE + 'W A S D Q E' + Fore.RESET + '\t\t\t Move camera')
	print(Fore.BLUE + 'LEFT SHIFT + MOUSE MOVE' + Fore.RESET + '\t\t Rotate camera')
	print()
	print(Fore.BLUE + 'ARROWS/HOME/END' + Fore.RESET + '\t\t\t Move particle generator')
	print(Fore.BLUE + 'LEFT CONTROL + MOUSE MOVE' + Fore.RESET + '\t Move particle generator')
	print()
	print(Fore.BLUE + 'PAGEUP/PAGEDOWN' + Fore.RESET + '\t\t\t Increase/decrease particle size')
	print(Fore.BLUE + 'P' + Fore.RESET + '\t\t\t\t Toggle between perspective/orthographic projection')
	print(Fore.BLUE + 'Z' + Fore.RESET + '\t\t\t\t Toggle spawning particles in sphere/cube')
	print(Fore.BLUE + 'L' + Fore.RESET + '\t\t\t\t Toggle particle lifetime decay on/off')
	print(Fore.BLUE + 'T' + Fore.RESET + '\t\t\t\t Toggle DOGE texture on/off')
	print(Fore.BLUE + 'X' + Fore.RESET + '\t\t\t\t Toggle particle shrinking on/off')
	print(Fore.BLUE + 'TAB' + Fore.RESET + '\t\t\t\t Select next particle mode')
	print(Fore.BLUE + 'C' + Fore.RESET + '\t\t\t\t Select next color profile')
	print()
	print(Fore.BLUE + 'ESC' + Fore.RESET + '\t\t\t\t Terminate')
	print()
	quit()

def parse_number(expr):
	try:
		return int(expr)
	except ValueError:
		terminate_with_usage()

def main():
	if len(sys.argv) < 2:
		terminate_with_usage()

	n_particles = parse_number(sys.argv[1])
	if n_particles <= 0:
		terminate_with_usage()

	try:
		particle_system = ParticleSystem(n_particles)
		particle_system.loop()
	except IOError as e:
		print(Style.BRIGHT + Fore.RED + 'I/O Error: ' + Style.RESET_ALL + Fore.RESET + str(e))
	except ParticleSystemException as e:
		print(Style.BRIGHT + Fore.RED + 'ParticleSystemException: ' + Style.RESET_ALL + Fore.RESET + str(e))

if __name__ == '__main__':
	main()
