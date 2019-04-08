# Run this script:
# source env.sh

# Set env variable with path to glfw/lib, so the python module glfw can find it

GLFW_PATH="$(brew --prefix glfw)/lib"

if [ -z "$DYLD_LIBRARY_PATH" ]
then
	export DYLD_LIBRARY_PATH="$GLFW_PATH"
else
	DYLD_LIBRARY_PATH="$DYLD_LIBRARY_PATH:$GLFW_PATH"
fi
