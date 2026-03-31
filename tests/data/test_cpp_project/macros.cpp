#include "macros.h"

#define CALL_FUNCTION(fn, arg) fn(arg)
#define CALL_METHOD(obj, method, arg) obj.method(arg)

namespace TestNamespace {

void macroTargetFunction(int x) {
  // Implementation
}

void MyClass::method(int x) {
  // Implementation
}

void testMacros() {
  // Call through macro
  CALL_FUNCTION(macroTargetFunction, 42);

  MyClass obj;
  CALL_METHOD(obj, method, 10);
}

}  // namespace TestNamespace

// Made with Bob
