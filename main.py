from math import cos, sin
from random import random
from typing import Optional

import cv2
import numpy as np
from numpy.polynomial.polynomial import polyvander


class Movable:
    def __init__(self, x0, y0, vx0, vy0, color, scene: 'Scene'):
        self.x = x0
        self.y = y0
        self.vx = vx0
        self.vy = vy0
        self.color = color
        self.scene = scene

    def update_position(self):
        self.x += self.vx
        self.y += self.vy

    def set_x(self, val):
        self.x = val

    def set_y(self, val):
        self.y = val

    def set_vx(self, val):
        self.vx = val

    def set_vy(self, val):
        self.vy = val

    def draw(self, img: np.ndarray):
        pass


class Circle(Movable):
    def __init__(self, radius, color, x0, y0, vx0, vy0, scene: 'Scene'):
        self.radius = radius
        super().__init__(x0=x0, y0=y0, vx0=vx0, vy0=vy0, color=color, scene=scene)
        self.scene.circle = self

    def draw(self, img: np.ndarray):
        cv2.circle(img, (int(self.x), int(self.y)), self.radius, self.color, -1)

    def out_of_scene(self, scene: 'Scene'):
        return (self.x > scene.width or self.x < 0) or (self.y > scene.height or self.y < 0)


class Tracker:
    def __init__(self, plane: 'Plane'):
        self.scene = plane.scene
        self.plane = plane
        self.coords = []
        self.polynom = None  # type: Optional[np.poly1d]

    def extract_coords(self, img):
        m = cv2.moments(img, True)
        if m['m00']:
            y, x = m['m01'] / m['m00'], m['m10'] / m['m00'] + self.scene.width / 3
            self.coords.append((x, y))

    def estimate_parabola(self):
        if len(self.coords) > 3:
            try:
                data = self.data
                B = polyvander(data[:, 0], 2)
                C = np.linalg.inv(B.T @ B) @ B.T @ data[:, 1]
                self.polynom = np.poly1d(C[::-1])
            except np.linalg.LinAlgError:
                self.polynom = None
        else:
            self.polynom = None

    @property
    def data(self):
        return np.array(self.coords)

    def estimate_position(self):
        if self.polynom:
            return self.polynom(self.scene.width) - self.plane.length / 2
        else:
            return self.scene.height / 2


class Plane(Movable):

    def __init__(self, length, width, color, x0, y0, vy0, scene: 'Scene'):
        self.length = length
        self.width = width
        super().__init__(x0=x0, y0=y0, vx0=0, vy0=vy0, color=color, scene=scene)
        self.tracker = Tracker(self)
        self.scene.plane = self
        # cv2.createTrackbar('plane pos', self.scene.window_name, int(self.scene.height / 2),
        #                    self.scene.height - self.length, lambda pos: self.set_y(pos))

    @property
    def vx(self):
        return 0

    @vx.setter
    def vx(self, val):
        pass

    def circle_catched(self, circle: Circle):
        return (circle.x + circle.radius) >= self.x and self.y <= circle.y <= (self.y + self.length)

    def change_position(self):
        self.tracker.extract_coords(self.scene.central_img[..., -1])
        self.tracker.estimate_parabola()
        y = self.tracker.estimate_position()
        self.y = max(min(y, self.scene.height - self.length), 0)

    def draw(self, img: np.ndarray):
        cv2.rectangle(img, (int(self.x), int(self.y)), (int(self.x + self.width), int(self.y + self.length)),
                      self.color, -1)


class Canon(Movable):
    def __init__(self,
                 angle,  # direction angle
                 length, width,  # dimensions
                 color,
                 launch_speed,
                 x0, y0,  # lower left coordinates
                 scene: 'Scene'
                 ):
        self.angle = angle  # radians
        self.length = length  # pixels
        self.width = width  # pixels
        self.launch_speed = launch_speed  # pixels per cycle
        self.circle_color = (0, 0, 255)
        super().__init__(x0=x0, y0=y0, vx0=0, vy0=0, color=color, scene=scene)
        self.scene.canon = self
        # cv2.createTrackbar('canon angle', self.scene.window_name, 0, 15,
        #                    lambda angle: self.set_angle(-np.radians(angle)))

    @property
    def vx(self):
        return 0

    @vx.setter
    def vx(self, val):
        pass

    @property
    def vy(self):
        return 0

    @vy.setter
    def vy(self, val):
        pass

    def shoot(self, angle):
        x0, y0 = self.launch_point()
        self.angle = angle
        return Circle(
            radius=int(self.width / 2),
            x0=x0, y0=y0,
            vx0=self.launch_speed * cos(self.angle),
            vy0=self.launch_speed * sin(self.angle),
            color=self.circle_color,
            scene=self.scene
        )

    @property
    def box(self):
        x1, y1 = self.x, self.y
        x2, y2 = x1 - self.width * sin(self.angle), y1 + self.width * cos(self.angle)
        x3, y3 = x2 + self.length * cos(self.angle), y2 + self.length * sin(self.angle)
        x4, y4 = x1 + self.length * cos(self.angle), y1 + self.length * sin(self.angle)
        return np.array([[x1, y1],
                         [x2, y2],
                         [x3, y3],
                         [x4, y4]]).astype(np.int)

    def launch_point(self):
        _, _, p3, p4 = self.box
        x0, y0 = (p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2
        return int(x0), int(y0)

    def draw(self, img: np.ndarray):
        cv2.drawContours(img, [self.box], -1, self.color, -1)
        # x, y = self.trajectory
        # img[y, x] = self.color

    @property
    def trajectory(self):
        vx, vy = self.launch_speed * cos(self.angle), self.launch_speed * sin(self.angle)
        x0, y0 = self.launch_point()
        x = np.mgrid[:self.scene.width - x0]
        t = x / vx
        y = y0 + vy * t + self.scene.g / 2 * t ** 2
        np.clip(y, 0, self.scene.height - 1, y)
        return x + x0, y.astype(np.int)

    def set_angle(self, angle):
        self.angle = angle


class Scene:
    def __init__(self, height, width,
                 canon: Optional[Canon] = None,
                 plane: Optional[Plane] = None,
                 window_name='Scene',
                 g=.0,
                 delay=25):
        self.shape = [height, width, 3]
        self.canon = canon
        self.circle = None
        self.plane = plane
        self.window_name = window_name
        self.g = g  # gravity velocity
        self.delay = delay
        self.img = np.zeros(self.shape)
        cv2.namedWindow(self.window_name)

    @property
    def height(self):
        return self.shape[0]

    @height.setter
    def height(self, val):
        self.shape[0] = val
        self.img = np.zeros(self.shape)

    @property
    def width(self):
        return self.shape[1]

    @width.setter
    def width(self, val):
        self.shape[1] = val
        self.img = np.zeros(self.shape, dtype=np.uint8)

    def clear_img(self):
        self.img = np.zeros(self.shape)

    @property
    def central_img(self):
        return self.img[:, int(self.width / 3):int(self.width * 2 / 3)]

    def update(self):
        self.clear_img()
        self.circle.update_position()
        self.plane.update_position()

    def show(self):
        cv2.line(self.img, (int(self.width / 3), 0), (int(self.width / 3), self.height), (255, 0, 0), 1)
        cv2.line(self.img, (int(2 * self.width / 3), 0), (int(2 * self.width / 3), self.height), (255, 0, 0), 1)
        self.circle.draw(self.img)
        self.plane.draw(self.img)
        self.canon.draw(self.img)
        cv2.imshow(self.window_name, self.img)

    def run(self):
        self.canon.shoot(random() * np.radians(-15))
        while (keyboard := cv2.waitKey(self.delay)) != 27:
            self.plane.change_position()
            self.update()
            self.circle.vy += self.g
            self.show()
            if self.plane.circle_catched(self.circle):
                print('success')
            if self.circle.out_of_scene(self):
                canon.shoot(random() * np.radians(-15))
                self.plane.tracker.coords = []
        cv2.destroyWindow(self.window_name)


if __name__ == '__main__':
    img_shape = (600, 300)
    scene = Scene(img_shape[1], img_shape[0], g=0.1, delay=25)
    canon = Canon(np.radians(-15), 30, 10, (127, 127, 0), 10, 0, img_shape[1] / 2, scene)
    plane = Plane(30, 5, (127, 0, 127), img_shape[0] - 2.5, img_shape[1] / 2, 0, scene)
    scene.run()
