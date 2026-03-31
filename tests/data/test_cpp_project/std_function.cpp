#include "std_function.h"
#include <functional>

namespace TestNamespace {

void targetFunction(int x) {
  // Implementation
}

void anotherTarget(int x) {
  // Implementation
}

void useStdFunction() {
  // Direct function assignment
  std::function<void(int)> fn1 = targetFunction;
  fn1(42);
  
  // Lambda assignment
  std::function<void(int)> fn2 = [](int x) { };
  fn2(10);
  
  // Reassignment
  std::function<void(int)> fn3 = targetFunction;
  fn3(1);
  fn3 = anotherTarget;
  fn3(2);
  
  // Address-of assignment
  std::function<void(int)> fn4 = &targetFunction;
  fn4(99);
}

void passFunctionAsParameter(std::function<void(int)> callback) {
  callback(5);
}

void testFunctionParameter() {
  passFunctionAsParameter(targetFunction);
  passFunctionAsParameter([](int x) { });
}

} // namespace TestNamespace

// Made with Bob
