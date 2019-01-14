#version 400 core

layout (location = 0) in vec4		position;
layout (location = 1) in vec4		color_;
layout (location = 2) in float		lifetime_;

out vec4							color;
out float							lifetime;
out float							distance_from_mouse;

uniform mat4						model;
uniform mat4						view;
uniform mat4						projection;

uniform float						mouse_x;
uniform float						mouse_y;

uniform float						point_size;
uniform bool						is_shrinking;

void main()
{
	// Calculate vertex position in clip space
	gl_Position = projection * view * model * vec4(position.xyz, 1.0f);

	// Calculate vertex position in NDC space, and compare it to mouse NDC position
	vec2 ndc_position;

	ndc_position.x = gl_Position.x / gl_Position.w;
	ndc_position.y = gl_Position.y / gl_Position.w;

	vec2 mouse_ndc_position = vec2(mouse_x, mouse_y);

	distance_from_mouse = distance(ndc_position, mouse_ndc_position);
	color = vec4(color_.xyz, 1.0f);
	lifetime = lifetime_;

	// Set particle size
	gl_PointSize = point_size;
	if (is_shrinking)
		gl_PointSize *= lifetime_;
}
