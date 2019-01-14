/*
	Return a random unsigned long
*/
static ulong rand_ulong(__global ulong* seed)
{
	ulong value = *seed * 1103515245 + 12345;

	*seed = value;
	return value;
}

/*
	Return a random float in range [0, 1]
*/
static float rand_float(__global ulong* seed)
{
	return (float)rand_ulong(seed) / ULONG_MAX;
}

/*
	Return a random float in range [a, b]
*/
static float rand_float_in_range(global ulong* seed, float a, float b)
{
	float	x = rand_float(seed);

	return (b - a) * x + a;
}

/*
	Get random position in a cube of length 1 at origin
*/
static float4 get_position_in_cube(
	__global ulong* seed)
{
	float4 position;

	position.x = rand_float_in_range(seed, -0.5f, 0.5f);
	position.y = rand_float_in_range(seed, -0.5f, 0.5f);
	position.z = rand_float_in_range(seed, -0.5f, 0.5f);
	return position;
}

/*
	Get random position in a sphere of radius 0.5 at origin
*/
static float4 get_position_in_sphere(
	__global ulong* seed)
{
	float4 position = get_position_in_cube(seed);
	float radius = rand_float_in_range(seed, 0.0f, 0.5f);

	return (float4)(normalize(position.xyz), 0.0f) * radius;
}

static float4 get_position(
	__global ulong* seed,
	float4 generator_position,
	bool spawn_in_cube)
{
	if (spawn_in_cube)
		return generator_position + get_position_in_cube(seed);
	else
		return generator_position + get_position_in_sphere(seed);
}

static float4 get_direction(float4 source, float4 destination)
{
	float4 direction = destination - source;

	direction.w = 0.0f;
	return (normalize(direction));
}

/*
	color_profile_id
*/
# define	COLOR_CONFETTI			0
# define	COLOR_MONOCHROME		1
# define	COLOR_RED_AND_WHITE		2
# define	COLOR_CMY				3
# define	COLOR_RAINBOW_DASH		4

static float4 get_color(
	__global ulong* seed,
	int color_profile_id)
{
	const float4 RW_TABLE[] =
	{
		(float4)(1.0f, 0.0f, 0.0f, 0.0f),							// Red
		(float4)(1.0f, 1.0f, 1.0f, 0.0f),							// White
	};

	const float4 CMY_TABLE[] = 
	{
		(float4)(0.0f, 1.0f, 1.0f, 0.0f),							// Cyan
		(float4)(1.0f, 0.0f, 1.0f, 0.0f),							// Magenta
		(float4)(1.0f, 1.0f, 0.0f, 0.0f),							// Yellow
	};

	const float4 RAINBOW_TABLE[] =
	{
		(float4)(1.0f, 0.0f, 0.0f, 0.0f),							// Red
		(float4)(1.0f, 165.0f / 255.0, 0.0f, 0.0f),					// Orange
		(float4)(1.0f, 1.0f, 0.0f, 0.0f),							// Yellow
		(float4)(0.0f, 1.0f, 0.0f, 0.0f),							// Green
		(float4)(0.0f, 0.0f, 1.0f, 0.0f),							// Blue
		(float4)(75.0f / 255.0f, 0.0f, 130.0f / 255.0f, 0.0f),		// Indigo
		(float4)(128.0f / 255.0f, 0.0f, 128.0f / 255.0f, 0.0f),		// Purple
	};

	float4 color;

	switch (color_profile_id)
	{
		case COLOR_MONOCHROME:
			color = (float4)(0.0f, 1.0f, 0.0f, 0.0f);				// Green
			break;
		case COLOR_RED_AND_WHITE:
			color = RW_TABLE[rand_ulong(seed) % 2];
			break;
		case COLOR_CMY:
			color = CMY_TABLE[rand_ulong(seed) % 3];
			break;
		case COLOR_RAINBOW_DASH:
			color = RAINBOW_TABLE[rand_ulong(seed) % 7];
			break;
		default:
			color.x = rand_float(seed);
			color.y = rand_float(seed);
			color.z = rand_float(seed);
			break;
	}
	return color;
}

/*
	particle_mode_id
*/
# define	PARTICLE_STATIONARY				0
# define	PARTICLE_FALLING_DOWN			1
# define	PARTICLE_GRAVITY_FOUNTAIN		2
# define	PARTICLE_RADIAL_EXPLOSION		3
# define	PARTICLE_CHAOS_NOVA				4
# define	PARTICLE_VORTEX_ATTRACTOR		5

static void update_particle(
	int particle_mode_id,
	__global float4* position,
	__global float4* velocity,
	__global ulong* seed,
	float4 generator_position,
	bool is_gravity_on)
{
	switch (particle_mode_id)
	{
		case PARTICLE_FALLING_DOWN:
		{
			position->y += is_gravity_on ? 0.02f : -0.02f;
			break;
		}
		case PARTICLE_GRAVITY_FOUNTAIN:
		{
			velocity->y += is_gravity_on ? 0.001f : -0.001f;
			*position += *velocity;
			break;
		}
		case PARTICLE_RADIAL_EXPLOSION:
		{
			float4 direction = get_direction(generator_position, *position) * 0.01f;
			
			*position += direction;
			if (is_gravity_on)
				position->y += -0.02f;
			break;
		}
		case PARTICLE_CHAOS_NOVA:
		{
			position->x += rand_float_in_range(seed, -0.1f, 0.1f);
			position->y += rand_float_in_range(seed, -0.1f, 0.1f);
			position->z += rand_float_in_range(seed, -0.1f, 0.1f);
			if (is_gravity_on)
				position->y += -0.02f;
			break;
		}
		case PARTICLE_VORTEX_ATTRACTOR:
		{
			float4 direction = get_direction(*position, generator_position) * 0.001f;

			*velocity += direction;
			*position += *velocity;
			if (is_gravity_on)
				position->y += -0.02f;
			break;
		}
		default:
		{
			break;
		}
	}
}

static void init_particle(
	__global float4* position,
	__global float4* color,
	__global float4* velocity,
	__global ulong* seed,
	float4 generator_position,
	bool spawn_in_cube,
	int particle_mode_id,
	int color_profile_id)
{
	*position = get_position(seed, generator_position, spawn_in_cube);
	*color = get_color(seed, color_profile_id);
	*velocity = (float4)(0.0, 0.0, 0.0, 0.0);

	switch (particle_mode_id)
	{
		case PARTICLE_GRAVITY_FOUNTAIN:
		{
			float4 direction = get_direction(generator_position, *position) * 0.05f;

			direction.y = direction.y > 0.0f ? direction.y : -direction.y;
			*velocity = direction;
			break;
		}
		default:
		{
			break;
		}
	}
}

__kernel void update(
	__global float4* position,
	__global float4* color,
	__global float* lifetime,
	__global float4* velocity,
	__global ulong* seed,
	float4 generator_position,
	int spawn_in_cube,
	int is_decaying,
	int is_gravity_on,
	int particle_mode_id,
	int color_profile_id)
{
	size_t id = get_global_id(0);

	if (is_decaying)
		lifetime[id] -= 0.01f;

	if (lifetime[id] > 0.0f)
	{
		update_particle(particle_mode_id, &position[id], &velocity[id], &seed[id], generator_position, (bool)is_gravity_on);
	}
	else
	{
		lifetime[id] = 1.0f;
		init_particle(&position[id], &color[id], &velocity[id], &seed[id], generator_position, (bool)spawn_in_cube, particle_mode_id, color_profile_id);
	}
}

__kernel void init(
	__global float4* position,
	__global float4* color,
	__global float* lifetime,
	__global float4* velocity,
	__global ulong* seed,
	float4 generator_position,
	int spawn_in_cube,
	int particle_mode_id,
	int color_profile_id)
{
	size_t id = get_global_id(0);

	seed[id] = (ulong) id;
	seed[id] = rand_ulong(&seed[id]);

	lifetime[id] = rand_float(&seed[id]);
	init_particle(&position[id], &color[id], &velocity[id], &seed[id], generator_position, (bool)spawn_in_cube, particle_mode_id, color_profile_id);
}

__kernel void change_color(
	__global float4* color,
	__global ulong* seed,
	int color_profile_id)
{
	size_t id = get_global_id(0);

	color[id] = get_color(&seed[id], color_profile_id);
}
