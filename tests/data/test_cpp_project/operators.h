#pragma once
#include <iostream>
#include <vector>

namespace TestNamespace {

class Functor {
public:
  void operator()(int x);
};

class Point2D {
public:
  double x, y;
  Point2D(double x, double y) : x(x), y(y) {}
  Point2D operator+(const Point2D& other) const;
};

std::ostream& operator<<(std::ostream& os, const Point2D& p);

class ArrayContainer {
public:
  std::vector<int> data;
  int& operator[](size_t index);
};

} // namespace TestNamespace

void testOperators();

// Made with Bob
