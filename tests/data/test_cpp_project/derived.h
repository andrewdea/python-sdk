#pragma once
#include "base.h"

namespace TestNamespace {

// Derived class for inheritance testing
class Derived : public Base {
 public:
  Derived();
  ~Derived() override;
  
  // Override virtual methods
  void virtualMethod() override;
  int pureVirtualMethod() override;
  
  // New methods
  void derivedMethod();
  int getValue() const;

 private:
  int derivedValue;
};

// Multiple inheritance example
class Interface {
 public:
  virtual ~Interface() = default;
  virtual void interfaceMethod() = 0;
};

class MultiDerived : public Derived, public Interface {
 public:
  MultiDerived();
  void interfaceMethod() override;
  void multiMethod();
};

// Template specialization
template <typename T>
class Processor {
 public:
  T process(T input);
};

// Partial specialization for pointers
template <typename T>
class Processor<T*> {
 public:
  T* process(T* input);
};

}  // namespace TestNamespace

// Made with Bob
