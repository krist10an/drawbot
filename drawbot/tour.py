import math
import random
from drawbot.util import *

def total_length(path_order, dist_matrix):
	total = 0
	_from = 0
	_to = 1
	while _to < len(path_order):
		total += dist_matrix[path_order[_from]][path_order[_to]]
		_from += 1
		_to += 1

	return total

def calc_dist_matrix(paths):
	path_count = len(paths)
	# Set up arrray
	dist_matrix = [[0 for x in xrange(0, path_count)] for y in xrange(0, path_count)]
	for _from in xrange(0, path_count):
		for _to in xrange(0, path_count):
			start = paths[_from][-1].end
			x1 = start.real
			y1 = start.imag
			end = paths[_to][0].start
			x2 = end.real
			y2 = end.imag
			dist_matrix[_from][_to] = math.hypot(x2 - x1, y2 - y1)

	return dist_matrix

def original_optimize(path_count):
	return [x for x in xrange(0, path_count)]

def random_optimize(path_count):
	xxxx = [x for x in xrange(0, path_count)]
	random.shuffle(xxxx)
	return xxxx

def greedy_optimize(dist_matrix, path_count):
	path_order = []
	# All indexes available in ascending order
	available_list = [x for x in xrange(0, path_count)]

	# Iterate though all segments, and find shortest path to next segment
	for current_index in xrange(0, path_count):
		best_index = 0
		best_value = 99999999
		# Iterate though segments not already taken and find shortest path
		for available_index in xrange(0, len(available_list)):
			if dist_matrix[current_index][available_index] < best_value:
				best_index = available_index
				best_value = dist_matrix[current_index][available_index]

		# Add shortest path to list
		path_order.append(available_list[best_index])

		# The segment is now no longer available, so remove it:
		available_list.pop(best_index)

	return path_order

def all_swapped(original_tour):
	for i in range(0, len(original_tour)):
		for j in range(0, len(original_tour)):
			mycopy = list(original_tour)
			tmp = mycopy[i]
			mycopy[i] = mycopy[j]
			mycopy[j] = tmp
			yield mycopy

def hillclimb(dist_matrix, path_count, max_evaluations):
	# Set random start
	best_tour = random_optimize(path_count)
	best_score = total_length(best_tour, dist_matrix)

	num_evaluations = 1
	while num_evaluations < max_evaluations:
		move_made = False

		for next in all_swapped(best_tour):
			next_score = total_length(next, dist_matrix)
			num_evaluations += 1

			if next_score < best_score:
				best_tour = list(next)
				best_score = next_score
				move_made = True

		if not move_made:
			break
			# No move found, at local maximum

	#print "  Local maximum found eval=%d score=%.1f " % (num_evaluations, best_score)
	return (num_evaluations, best_score, best_tour)

def hillclimb_restart_optimize(dist_matrix, path_count, max_evaluations):
	"""
	Hillclimb with restart
	Based on the excellent description here:
	http://www.psychicorigami.com/2007/05/12/tackling-the-travelling-salesman-problem-hill-climbing/
	"""	
	best_tour=None
	best_score=0

	#print "Hillclimb start"
	num_evaluations=0
	while num_evaluations < max_evaluations:
		remaining_evaluations = max_evaluations - num_evaluations
		
		evaluated, score, found = hillclimb(dist_matrix, path_count, remaining_evaluations)

		num_evaluations += evaluated
		if score < best_score or best_tour is None:
			best_score = score
			best_tour = found

	#print "Hillclimb done evaluations=%s score=%.1f" % (num_evaluations, best_score)
	return best_tour
