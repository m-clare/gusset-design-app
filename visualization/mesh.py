import plotly.graph_objects as go


class PlateMesh(object):

    def __init__(self, x=None, y=None, z=None):

        self._type = 'mesh3d'
        self._x = x
        self._y = y
        self._z = z
        self._alphahull = 0
        self._color = 'grey'

    @property
    def type(self):
        return self._type

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = value

    @property
    def alphahull(self):
        return self._alphahull

    @property
    def color(self):
        return self._color

    @classmethod
    def from_geometry(cls, points):
        plate = cls()
        x = []
        y = []
        z = []
        for point in points:
            x.append(point[0])
            y.append(point[1])
            z.append(point[2])
        plate.x = x
        plate.y = y
        plate.z = z
        return plate

    @classmethod
    def from_data(cls):
        pass

    @classmethod
    def from_json(cls):
        pass

    def to_dict(self):
        return dict(type=self.type,
                    x=self.x, y=self.y, z=self.z,
                    alphahull=self.alphahull, color=self.color)

    def add_to_meshes(self, meshes):
        meshes.append(self.to_dict())
        return meshes


if __name__ == "__main__":
    pass