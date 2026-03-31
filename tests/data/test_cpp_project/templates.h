#ifndef TEMPLATES_H
#define TEMPLATES_H

// Primary class template
template <typename T>
class Container {
 public:
  T value;
  Container(T v) : value(v) {}
};

// Explicit specialization for int
template <>
class Container<int> {
 public:
  int value;
  int extra;
  Container(int v) : value(v), extra(0) {}
};

// Partial specialization for pointers
template <typename T>
class Container<T*> {
 public:
  T* value;
  Container(T* v) : value(v) {}
};

// Primary function template
template <typename T>
T add(T a, T b) {
  return a + b;
}

// Explicit specialization for double
template <>
double add<double>(double a, double b) {
  return a + b + 0.1;
}

#endif  // TEMPLATES_H

// Made with Bob
