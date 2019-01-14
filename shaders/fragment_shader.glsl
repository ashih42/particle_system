#version 400 core

in vec4					color;
in float				lifetime;
in float				distance_from_mouse;

out vec4				frag_color;

uniform sampler2D		doge_texture;
uniform bool			is_texture;

void main()
{
	if (is_texture)
		frag_color = texture(doge_texture, gl_PointCoord);
	else
		frag_color = color;

	vec4 near_mouse_color = vec4(1.0f, 1.0f, 1.0f, 1.0f);

	frag_color = mix(near_mouse_color, frag_color, distance_from_mouse);
	frag_color *= lifetime;
}
