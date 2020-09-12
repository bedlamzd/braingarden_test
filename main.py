from math import cos, sin

import cv2
import numpy as np


class Movable:
    def __init__(self, x0, y0, vx0, vy0, color):
        self.x = x0
        self.y = y0
        self.vx = vx0
        self.vy = vy0
        self.color = color

    def update_position(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, img: np.ndarray):
        pass


class Circle(Movable):
    def __init__(self, radius, color, x0, y0, vx0, vy0):
        self.radius = radius
        super().__init__(x0=x0, y0=y0, vx0=vx0, vy0=vy0, color=color)

    def draw(self, img: np.ndarray):
        cv2.circle(img, (int(self.x), int(self.y)), self.radius, self.color, -1)


class Plane(Movable):
    def __init__(self, length, width, color, x0, y0, vy0=0):
        self.length = length
        self.width = width
        super().__init__(x0=x0, y0=y0, vx0=0, vy0=vy0, color=color)

    @property
    def vx(self):
        return 0

    @vx.setter
    def vx(self, val):
        pass

    def circle_catched(self, circle: Circle):
        return (circle.x + circle.radius) >= self.x and (self.y - self.length) <= circle.y <= self.y

    def draw(self, img: np.ndarray):
        cv2.rectangle(img, (int(self.x), int(self.y)), (int(self.x + self.width), int(self.y + self.length)),
                      self.color, -1)


class Canon(Movable):
    def __init__(self,
                 angle,  # direction angle
                 length, width,  # dimensions
                 color,
                 launch_speed,
                 x0, y0  # lower left coordinates
                 ):
        self.angle = angle  # radians
        self.length = length  # pixels
        self.width = width  # pixels
        self.launch_speed = launch_speed  # pixels per cycle
        self.circle_color = (0, 0, 255)
        super().__init__(x0=x0, y0=y0, vx0=0, vy0=0, color=color)

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

    def shoot(self):
        _, _, p3, p4 = self.box
        x0, y0 = (p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2
        return Circle(
            radius=int(self.width / 2),
            x0=x0, y0=y0,
            vx0=self.launch_speed * cos(self.angle),
            vy0=self.launch_speed * sin(self.angle),
            color=self.circle_color
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

    def draw(self, img: np.ndarray):
        cv2.drawContours(img, [self.box], -1, self.color, -1)

    def set_angle(self, angle):
        self.angle = angle


class Scene:
    def __init__(self, height, width, canon: Canon, plane: Plane, window_name='Scene', vg=0, delay=25):
        self.shape = (height, width, 3)
        self.canon = canon
        self.circle = canon.shoot()
        self.plane = plane
        self.window_name = window_name
        self.vg = vg  # gravity velocity
        self.delay = delay
        self.img = np.zeros(self.shape)
        cv2.namedWindow(self.window_name)
        cv2.createTrackbar('canon angle', self.window_name, -np.degrees(self.canon.angle).astype(np.int), 15,
                           lambda angle: self.canon.set_angle(-np.radians(angle)))

    def update(self):
        self.circle.update_position()
        self.plane.update_position()

    def show(self):
        self.img = np.zeros(self.shape)
        cv2.line(self.img, (int(self.shape[1] / 3), 0), (int(self.shape[1] / 3), self.shape[0]), (255, 0, 0), 1)
        cv2.line(self.img, (int(2 * self.shape[1] / 3), 0), (int(2 * self.shape[1] / 3), self.shape[0]), (255, 0, 0), 1)
        self.circle.draw(self.img)
        self.plane.draw(self.img)
        self.canon.draw(self.img)
        cv2.imshow(self.window_name, self.img)

    def run(self):
        while (keyboard := cv2.waitKey(self.delay)) != 27:
            self.update()
            self.circle.vy += self.vg
            self.show()
            if self.plane.circle_catched(self.circle):
                print('success')
            if self.circle.x > self.shape[1] or self.circle.y > self.shape[0]:
                self.circle = canon.shoot()
        cv2.destroyWindow(self.window_name)


if __name__ == '__main__':
    img_shape = (600, 300)
    canon = Canon(np.radians(-15), 30, 10, (127, 127, 0), 30, 0, img_shape[1] / 2)
    plane = Plane(30, 5, (127, 0, 127), img_shape[0] - 2.5, img_shape[1] / 2, 0)
    scene = Scene(img_shape[1], img_shape[0], canon, plane, vg=1, delay=25)
    scene.run()
