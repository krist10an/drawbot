import pysvg
import pysvg.parser
import pysvg.shape
import svg.path.parser
import svg.path.path

from drawbot.util import *

def decode_path(path_string):
	try:
		paths = svg.path.parser.parse_path(path_string)
		#print "Start", paths[0].start, "end", paths[len(paths)-1].end
		return paths
	except ValueError as e:
		print "Invalid path", e
		return []

def decode_polyline(points_str):
	#print "Decode '%s'" % points_str
	lines = []
	for pt in points_str.strip().split(" "):
		try:
			x, y = pt.split(",")
			x = float(x)
			y = float(y)
		except ValueError as e:
			if pt:
				print "Error decoding polyline '%s' " % pt
			continue
		lines.append(complex(x,y))

	polyline_segments = svg.path.Path()
	last_pos = lines[0]
	for next_pos in lines[1:]:
		polyline_segments.append(svg.path.Line(last_pos, next_pos))
		last_pos = next_pos

	return polyline_segments

def decode_rect(rect):
	pts = rect.getEdgePoints()
	#print "Hurra", rect, pts
	pts = [complex(x,y) for x,y in pts]
	#print pts
	rect_segments = svg.path.Path()
	rect_segments.append(svg.path.Line(pts[0], pts[1]))
	rect_segments.append(svg.path.Line(pts[1], pts[2]))
	rect_segments.append(svg.path.Line(pts[2], pts[3]))
	rect_segments.append(svg.path.Line(pts[3], pts[0]))
	return rect_segments

def draw_polyline(painter, lines):
	for x,y in lines:
		painter.drawto(x,y, [0,255,0])

def get_paths_from_svg(top, level=0):
	segments = []
	i = 0
	while 1:
		try:
			element = top.getElementAt(i)
			i += 1

			if isinstance(element, pysvg.core.TextContent):
				continue
			if isinstance(element, pysvg.gradient.pattern):
				continue
			if isinstance(element, pysvg.text.text):
				continue
#			if isinstance(element, pysvg.text.tspan):
#				continue

			#print " "*level, element
		except IndexError:
			# We are done
			break

		ssegments = get_paths_from_svg(element, level+1)
		segments.extend(ssegments)

		if isinstance(element, pysvg.shape.path):
			# Decode path and find start and end points
			path = decode_path(element.get_d())
			segments.append(path)
		elif isinstance(element, pysvg.shape.polygon):
			# Decode polygon
			path = decode_polyline(element.get_points())
			segments.append(path)
		elif isinstance(element, pysvg.shape.rect):
			path = decode_rect(element)
			segments.append(path)
		else:
			print " "*level, "No support for element:", element

	return segments

def estimate_bounds_for_paths(all_paths):
	bounds = Bounds()
	for path in all_paths:
		for seg in path:
			bounds.include_im_point(seg.start)
			bounds.include_im_point(seg.end)
	return bounds
