import sys
import os
import pygame
import math

import serial

import struct

import svg.path.path

from drawbot.tour import *
from drawbot.input import *
from drawbot.util import *

def deg2rad(deg):
	return math.pi * deg/180

class DrawBot(object):
	"""
	Polar coordinates:

	             <-----x------->
	   motor 1  *<--------- distance -------->*   motor 2
	   	          \            |            /
	   	            \          |          /
	   	              \        y        /
	   	         alpha  \      |      /  beta
	   	                  \    |    /
	   	                    \  |  /
	   	                     \ | /
	   	                     (x,y)

	"""
	def __init__(self, distance, initial_alpha, initial_beta):
		self.distance = distance
		self.alpha = initial_alpha
		self.beta  = initial_beta

		# Calculate start position
		xxx, yyy = self.polar2xy(self.alpha, self.beta)
		self.reset(xxx, yyy)
		self.deltay = yyy
		print " * Start position values x,y=%f,%f a=%f,b=%f" % (self.x, self.y, self.alpha, self.beta)
		self.display_x_offset = 300
		self.distance_drawn = 0
		self.motor_init()

	def reset(self, x, y):
		self.x = x
		self.y = y

	def xy2polar(self, x, y):
		y2 = y + self.deltay
		alpha = math.sqrt((x)**2 + y2**2)
		beta  = math.sqrt((self.distance - x)**2 + y2**2)
		return (alpha, beta)

	def polar2xy(self, alpha, beta):
		xxx = float2int((alpha**2 - beta**2 + self.distance**2) / (2* self.distance))
		yyy = float2int(math.sqrt(alpha**2 - xxx**2))
		return (xxx, yyy)

	def draw_strings(self, screen, color=[100,100,100]):
		xxx, yyy = self.polar2xy(self.alpha, self.beta)
		ddx = self.display_x_offset
		pygame.draw.circle(screen, color, (ddx+xxx,yyy), 3)
		pygame.draw.line(screen, color, [ddx,0], [ddx+xxx, yyy])
		pygame.draw.line(screen, color, [ddx+self.distance,0], [ddx+xxx, yyy])

	def draw_outline_bounds(self, screen, bounds):
		self.draw_outline(screen, bounds.tl[0], bounds.tl[1], bounds.br[0], bounds.br[1])

	def draw_outline(self, screen, x1, y1, x2, y2):
		# Top left
		oa, ob = self.xy2polar(x1, y1)
		ox, oy = self.polar2xy(oa, ob)
		ox += self.display_x_offset

		# Bottom right
		sa, sb = self.xy2polar(x2, y2)
		sx, sy = self.polar2xy(sa, sb)
		sx += self.display_x_offset

		# Draw bounds
		pygame.draw.rect(screen, [0,0,0], [ox, oy, sx-ox, sy-oy], 1)

		# Draw Origo
		oa, ob = self.xy2polar(0, 0)
		ox, oy = self.polar2xy(oa, ob)
		pygame.draw.circle(screen, [255, 0, 0], (self.display_x_offset+ox, oy), 5)

	def drawto(self, x, y, z, screen, color=[0, 255, 0]):
		alpha, beta = self.xy2polar(x, y)

		diffa = alpha - self.alpha
		diffb = beta - self.beta

		nx, ny = self.polar2xy(alpha, beta)
		distance = math.hypot(nx - self.x, ny - self.y)
		self.distance_drawn += distance

		if z > 0:
			color = [0, 255, 0]

		# Draw line
		pygame.draw.line(screen, color, [self.display_x_offset + self.x, self.y], [self.display_x_offset + nx, ny], 1)

		self.debug_move(x, y, alpha, diffa, beta, diffb)
		self.motor_move(diffa, diffb, distance)

		# Update  current position
		self.alpha = alpha
		self.beta  = beta
		self.reset(nx, ny)

	def debug_move(self, x, y, alpha, diffa, beta, diffb):
		pass

	def motor_move(self, diffa, diffb, distance):
		pass

	def motor_init(self):
		pass

class DrawBotSimulator(DrawBot):
	def debug_move(self, x, y, alpha, diffa, beta, diffb):
		print "Move to x = %3d y=%3d A=%#3.1f + %.1f\t B=%3.1f + %.1f" % (x, y, alpha, diffa, beta, diffb)

	def motor_move(self, diffa, diffb, distance):
		# Simulate move:
		speed = 0.5
		pygame.time.wait(float2int(distance*speed))

	def motor_init(self):
		pass

# -- Simple Serial --
class DrawBotSerial(DrawBotSimulator):
	def __init__(self, ser, distance, initial_alpha, initial_beta):
		self.ser = ser
		super(DrawBotSerial, self).__init__(distance, initial_alpha, initial_beta)

	def motor_init(self):
		stepsp = 4096 / (2*math.pi*4)
		self.stepsprmm = float2int(stepsp)

	@staticmethod
	def send_axis(ser, num):
		if num < 0:
			ser.write(chr(1))
		else:
			ser.write(chr(0))
		ser.write(struct.pack("H", abs(float2int(num))))

	@staticmethod
	def send_motor_move(ser, m1, m2):
		if ser is None:
			#print "No serial, not moving motor"
			return

		DrawBotSerial.send_axis(ser, m1)
		DrawBotSerial.send_axis(ser, m2)

		x = ser.read()

		if x != "O":
			print "Non OK received from motors, something is wrong"

		x = ser.read()

		if x != "K":
			print "Something is wrong!"

	def motor_move(self, diffa, diffb, distance):
		if self.ser is not None:
			DrawBotSerial.send_motor_move(self.ser, diffa*self.stepsprmm, diffb*self.stepsprmm)
		else:
			speed = 2
			pygame.time.wait(float2int(distance*speed))

class DrawBotGcode(DrawBotSimulator):
	def __init__(self, ser, distance, initial_alpha, initial_beta):
		self.ser = ser
		super(DrawBotGcode, self).__init__(distance, initial_alpha, initial_beta)

	def send_gcode(self, gcode):
		print "Gcode", gcode
		if self.ser:
			self.ser.write(gcode.strip() + "\n")
			#pygame.time.wait(100)
			resp = self.ser.readline()
			if resp.strip() != "ok":
				print "Motor error:", resp

	def motor_init(self):
		# Wake up grbl
		if self.ser:
			self.ser.write("\r\n\r\n")
		#import time
		#time.sleep(2) # Wait for grbl to initialize
		pygame.time.wait(200)
		if self.ser:
			self.ser.flushInput() # Flush startup text in serial input
		print "Initialized"
		self.stepsprmm = 1 # Scale factor
		self.invert_alpha = True
		self.invert_beta = True
		self.send_gcode("G91") # Relative positioning
		self.send_gcode("G21") # Set unit to millimeters

	def motor_move(self, diffa, diffb, distance):
		# Invert axis
		if self.invert_alpha:
			diffa = - diffa
		if self.invert_beta:
			diffb = - diffb
		self.send_gcode("G1 X%.1f Y%.1f F100" % (diffa*self.stepsprmm, diffb*self.stepsprmm))

done = False
def is_done():
	global done
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				done = True

	return done

scale = 0.5
def segment_iterator(path):
	global scale
	for segment in path:
		if isinstance(segment, svg.path.path.Line):
			iterations = 1
		else:
			iterations = 5

		points = [segment.point(float(x)/iterations) for x in range(0, iterations+1)]
		x, y = im2xy(points[0])
		# Move with pen up
		yield float2int(x*scale), float2int(y*scale), 1
		for xy in points[1:]:
			x, y = im2xy(xy)
			# Move with pen down
			yield float2int(x*scale), float2int(y*scale), 0

def draw_tour(drawbot, tour, all_paths, screen, background, blit=True):
	for segment_num in tour:
		if is_done():
			break

		path = all_paths[segment_num]
		for x,y,z in segment_iterator(path):
			drawbot.drawto(x, y, z, background, [100,100,255])

			if blit:
				screen.blit(background, (0,0))
				# Draw strings
				drawbot.draw_strings(screen)
				pygame.display.flip()

			if is_done():
				break

def navigate_to_start(bot, clock):
	print "---------Ready to draw-----"
	print "Position the gondola using:"
	print "  Left/Right and Up/Down"
	print ""
	print "Press Enter to start. ESC to cancel"
	start = False
	while not start and not is_done():
		clock.tick(60)

		keystate = pygame.key.get_pressed()
		dist = 10
		mx = 0
		my = 0
		if keystate[pygame.K_RETURN]:
			start = True
		if keystate[pygame.K_UP]:
			mx = dist
		if keystate[pygame.K_DOWN]:
			mx = -dist
		if keystate[pygame.K_LEFT]:
			my = dist
		if keystate[pygame.K_RIGHT]:
			my = -dist

		if abs(mx) > 0 or abs(my) > 0:
			print "Move", mx, my
			bot.motor_move(mx, my, 0)

def main(filename, port, m_type, m_distance, m_initial_alpha, m_initial_beta, max_size):
	global scale

	if max_size is None:
		max_size = m_distance * 0.8

	print "---- Welcome to DrawBot ----"
	print "- Parsing SVG", filename
	svg_image = pysvg.parser.parse(filename, debug=False)
	all_paths = get_paths_from_svg(svg_image)
	# start = complex(200,0)
	# stop = complex(200,3)
	# all_paths.insert(0, svg.path.path.Path(svg.path.Line(start, stop)))
	bounds = estimate_bounds_for_paths(all_paths)

	print "- Parsing SVG done"
	print " - SVG image size %s x %s" % (svg_image.get_width(), svg_image.get_height())
	print " - Estimated bounds:", bounds, bounds.width(), bounds.height()
	print " - Max size:", max_size
	if bounds.width() > max_size:
		scale = max_size / bounds.width()
		print "  - Scaling to:", scale
		bounds = bounds * scale

	path_count = len(all_paths)
	print "- Calculating distance. Path count=", path_count
	dist_matrix = calc_dist_matrix(all_paths)

	print "- Optimizing"
	optimized_tour = hillclimb_restart_optimize(dist_matrix, path_count, 75000)

	pygame.init()

	size = [1200, 600]
	screen = pygame.display.set_mode(size)
	pygame.display.set_caption("DrawBot")
	screen.fill([255, 255, 255])
	pygame.display.flip()

	background = pygame.surface.Surface(size)
	background.fill([255, 255, 255])

	painter = DrawBot(m_distance, m_initial_alpha, m_initial_beta)
	draw_tour(painter, optimized_tour, all_paths, background, background, blit=False)
	screen.blit(background, (300, 0))
	pygame.display.flip()
	background.fill([255, 255, 255])

	clock = pygame.time.Clock()

	print "- Opening serial port", port
	try:
		ser = serial.Serial(port-1)
		print ser
	except:
		print "ERROR: Unable to open serial port", port
		ser = None

	if m_type == "serial":
		drawbot = DrawBotSerial(ser, m_distance, m_initial_alpha, m_initial_beta)
	elif m_type == "gcode":
		drawbot = DrawBotGcode(ser, m_distance, m_initial_alpha, m_initial_beta)
	else:
		raise Exception("Unkown machine type" + m_type)
	drawbot.draw_outline_bounds(screen, bounds)
	drawbot.draw_strings(screen)
	pygame.display.flip()

	navigate_to_start(drawbot, clock)

	screen.fill([255, 255, 255])
	drawbot.draw_outline_bounds(background, bounds)

	draw_tour(drawbot, optimized_tour, all_paths, screen, background)

	if done:
		print "Aborted"
	else:
		print "Drawing completed."
		print "Distance moved:", drawbot.distance_drawn

	while not is_done():
		# This limits the while loop to a max of 10 times per second.
		# Leave this out and we will use all CPU we can.
		clock.tick(10)

	pygame.quit()

if __name__ == "__main__":
	import argparse
	import json

	parser = argparse.ArgumentParser(description='Run DrawBot.')
	parser.add_argument('machine', metavar='machine', type=str, help='Machine description JSON')
	parser.add_argument('filename', metavar='filename', type=str, help='SVG file to use as input')
	parser.add_argument('-p', '--port', dest='port', type=int, action='store', default=None, help='COM port to use')
	parser.add_argument('-s', '--size', dest='size', type=float, action='store', default=None, help='Output size (mm)')

	args = parser.parse_args()
	try:
		cstr = open(args.machine).read()
	except IOError:
		print "Unable to open machine file", args.machine
		sys.exit(1)

	config = json.loads(cstr)
	_type = config["type"]
	_distance = config["distance"]
	_alpha = config["alpha"]
	_beta = config["beta"]

	main(args.filename, args.port, _type, _distance, _alpha, _beta, args.size)
