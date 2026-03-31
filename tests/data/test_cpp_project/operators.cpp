#include "operators.h"

namespace TestNamespace {

// Functor with operator()
void Functor::operator()(int x) {
  // Implementation
}

// Arithmetic operator
Point2D Point2D::operator+(const Point2D& other) const {
  return Point2D(x + other.x, y + other.y);
}

// Stream operator
std::ostream& operator<<(std::ostream& os, const Point2D& p) {
  os << "(" << p.x << ", " << p.y << ")";
  return os;
}

// Subscript operator
int& ArrayContainer::operator[](size_t index) {
  return data[index];
}

} // namespace TestNamespace

void testOperators() {
  TestNamespace::Functor f;
  f(42);  // operator() call
  
  TestNamespace::Point2D p1(1, 2);
  TestNamespace::Point2D p2(3, 4);
  auto p3 = p1 + p2;  // operator+ call
  
  std::cout << p3;  // operator<< call
  
  TestNamespace::ArrayContainer c;
  c[0] = 10;  // operator[] call
}

// Made with Bob
