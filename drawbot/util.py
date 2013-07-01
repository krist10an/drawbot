
def float2int(num):
	return int(round(num))

def im2xy(im):
	return (float2int(im.real), float2int(im.imag))


class Bounds(object):
	def __init__(self):
		self.tl = [9999,9999]
		self.br = [0,0]

	def include_point(self, x, y):
		self.tl[0] = min(self.tl[0], x)
		self.tl[1] = min(self.tl[1], y)
		self.br[0] = max(self.br[0], x)
		self.br[1] = max(self.br[1], y)

	def include_im_point(self, im):
		x, y = im2xy(im)
		self.include_point(x,y)

	def is_valid(self):
		return self.tl[0] < self.br[0] and self.tl[1] < self.br[1]

	def extend(self, bounds):
		if bounds.is_valid():
			self.include_point(bounds.tl[0], bounds.tl[1])
			self.include_point(bounds.br[0], bounds.br[1])

	def __repr__(self):
		return "Bounds[%d,%d - %d, %d]" % (self.tl[0], self.tl[1], self.br[0], self.br[1])

	def width(self):
		return self.br[0] - self.tl[0]

	def height(self):
		return self.br[1] - self.tl[1]

	def __mul__(self, val):
		b = Bounds()
		b.tl[0] = self.tl[0] * val
		b.tl[1] = self.tl[1] * val
		b.br[0] = self.br[0] * val
		b.br[1] = self.br[1] * val
		return b
