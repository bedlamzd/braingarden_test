// braingarden_test_cpp.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include <random>
#include <vector>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/highgui.hpp>

using namespace cv;
using namespace std;

float radians(float degrees) {
    return 3.14 * degrees / 180;
}

float degrees(float radians) {
    return 180 * radians / 3.14;
}

class Movable
{
protected:
    float x, y;
    float vx, vy;
    Scalar color;
    Scene scene;
public:

    Movable(float x0, float y0, float vx0, float vy0, Scalar clr, Scene sc) {
        x = x0;
        y = y0;
        vx = vx0;
        vy = vy0;
        color = clr;
        scene = sc;
    }

    void update_position() {
        x += vx;
        y += vy;
    }
    Scene get_scene() {
        return scene;
    }
    void set_x(float new_x) {
        x = new_x;
    }
    float get_x() {
        return x;
    }
    void set_y(float new_y) {
        y = new_y;
    }
    float get_y() {
        return y;
    }
    void draw(Mat img){}
};

class Canon : public Movable
{
protected:
    float angle, launch_speed;
    int length, width;
    float get_random_angle() {
        static default_random_engine e;
        static uniform_real_distribution<> dis(0, radians(15));
        return dis(e);
    }

public:
    Canon(float a, int l, int w, Scalar color, float l_s, float x0, float y0, Scene sc) : Movable(x0, y0, 0, 0, color, sc) {
        angle = a;
        length = l;
        width = w;
        this->color = color;
    };

    void shoot() {
        Point l_point = launch_point();
        angle = get_random_angle();
        Point lp = launch_point();
        Circle(width / 2, Scalar(0, 0, 255), lp.x, lp.y, launch_speed * cos(angle), launch_speed * sin(angle), scene);
    }

    Point launch_point() {
        Point* verts = &box();
        Point l_point = (verts[2] + verts[3]) / 2;
        return l_point;
    }

    Point box() {
        RotatedRect rect = RotatedRect(
            Point(x, y),
            Size(length, width),
            angle
        );
        Point2f verts2f[4];
        rect.points(verts2f);
        Point verts[4];
        for (int i = 0; i < 4; ++i)
            verts[i] = verts2f[i];
        return *verts;
    }


    void draw(Mat img) {
        fillConvexPoly(img, &box(), 4, color);
    }

};

class Tracker {
protected:
    Scene scene;
    Plane *plane;
    vector<Point> coords;
public:
    Tracker(Plane p) {
        plane = &p;
        scene = (*plane).get_scene();
    }

    void extract_coords(Mat img) {
        Moments m = moments(img, true);
        if (m.m00 != 0)
        {
            coords.push_back(Point(m.m10 / m.m00 + scene.get_width() / 3, m.m01 / m.m00));
        }
    }
    void estimate_parabola();
    float estimate_position();
};

class Circle : public Movable
{
protected:
    float radius;
public:
    Circle(float r, Scalar color, float x0, float y0, float vx0, float vy0, Scene sc) :Movable(x0, y0, vx0, vy0, color, sc) {
        radius = r;
        scene.set_circle(*this);
    }
    void draw(Mat img) {
        circle(img, Point(x, y), radius, color, -1);
    }
    bool out_of_scene() {
        return (x > scene.get_width() or x < 0) or (y > scene.get_height() or y < 0);
    }
};
class Plane : public Movable
{
protected:
    int length, width;
    Tracker *tracker;

public:
    Plane(int l, int w, Scalar clr, float x0, float y0, float vy0, Scene sc) :Movable(x0, y0, 0, vy0, clr, sc) {
        length = l;
        width = w;
        tracker = &Tracker(*this);
        scene.set_plane(*this);
    }
    bool circle_caught(Circle c) {
        
    }

    void update_position() {
        
        (*tracker).extract_coords(scene.center_img());
    }
};

class Scene
{
protected:
    Size size;
    Canon *canon;
    Circle *circle;
    Plane *plane;
    String window_name;
    float g;
    int delay;
    Mat img;
public:
    Scene(int height = 300, int width = 600, String window_name = "Scene", float g = 0, int delay = 25) {
        size = Size(width, height);
        this->window_name = window_name;
        this->g = g;
        this->delay = delay;
        namedWindow(this->window_name);
        img = Mat::zeros(size, CV_8UC3);
    }
    
    void set_plane(Plane p) {
        plane = &p;
    }

    void set_circle(Circle c) {
        circle = &c;
    }

    void set_canon(Canon c) {
        canon = &c;
    }

    int get_height() {
        return size.height;
    }
    int get_width() {
        return size.width;
    }
    Mat center_img() {
        Mat r;
        Rect rect(get_width()/3, 0, get_width()/3, get_height());
        extractChannel(img(rect), r, 2);
        return r;
    }
    void clear_img() {
        img = Mat::zeros(size, CV_8UC3);
    }
    void update() {
        clear_img();
        (*circle).update_position();
        (*plane).update_position();
    }
    void show() {
        (*circle).draw(img);
        (*plane).draw(img);
        (*canon).draw(img);
        imshow(window_name, img);
    }
    void run() {
        (*canon).shoot();
    }
};

int main()
{
    int w = 600, h = 300;
    Scene s = Scene(h, w, "Scene", 0.1, 25);
    Canon canon = Canon(0, 30, 10, Scalar(127, 127, 0), 10, 5, h / 2, s);
    Plane p = Plane(30, 5, Scalar(127, 0, 127), w - 3, h / 2, 0, s);
    s.run();
}