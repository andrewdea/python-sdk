#include "derived.h"

namespace TestNamespace {

// Derived class implementation
Derived::Derived() : Base(), derivedValue(42) {}

Derived::~Derived() {}

void Derived::virtualMethod() {
  // Override implementation
  Base::virtualMethod();  // Call base class method
}

int Derived::pureVirtualMethod() {
  return derivedValue;
}

void Derived::derivedMethod() {
  // Derived-specific method
  nonVirtualMethod();  // Call inherited method
}

int Derived::getValue() const {
  return derivedValue;
}

// MultiDerived implementation
MultiDerived::MultiDerived() : Derived() {}

void MultiDerived::interfaceMethod() {
  // Interface implementation
}

void MultiDerived::multiMethod() {
  // Multi-derived specific method
  virtualMethod();  // Call inherited virtual method
  derivedMethod();  // Call derived method
}

// Template implementations
template <typename T>
T Processor<T>::process(T input) {
  return input;
}

template <typename T>
T* Processor<T*>::process(T* input) {
  return input;
}

// Explicit instantiations
template class Processor<int>;
template class Processor<double>;
template class Processor<int*>;

}  // namespace TestNamespace

// Made with Bob
