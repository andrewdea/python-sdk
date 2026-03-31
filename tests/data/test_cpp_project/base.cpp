#include "base.h"
#include <cmath>

namespace TestNamespace {

// Base class implementation
Base::Base() : baseValue(0) {}

Base::~Base() {}

void Base::virtualMethod() {
  // Virtual method implementation
}

void Base::nonVirtualMethod() {
  // Non-virtual method implementation
}

// Point struct implementation
Point::Point(double x, double y) : x(x), y(y) {}

double Point::distance() const {
  return std::sqrt(x * x + y * y);
}

// Free function implementations
void freeFunction(int x) {
  // Free function implementation
}

int calculateSum(int a, int b) {
  return a + b;
}

}  // namespace TestNamespace

// Made with Bob
