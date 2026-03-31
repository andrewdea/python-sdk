#include "base.h"
#include "derived.h"
#include "function_pointers.h"
#include "operators.h"
#include "std_function.h"
#include <iostream>
#include <memory>

using namespace TestNamespace;

// Helper function for testing
void helperFunction() {
  std::cout << "Helper function called\n";
}

// Function using templates
template <typename T>
void processValue(T value) {
  Container<T> container(value);
  std::cout << "Processed: " << container.getData() << "\n";
}

// Inter-file call testing
void testInterFileCalls() {
  // Call free function from base.cpp
  freeFunction(10);
  int sum = calculateSum(5, 7);
  
  // Call through function pointer
  executeCallback(callbackFunction, 42);
  
  // Use callback handler
  CallbackHandler handler;
  handler.setCallback(anotherCallback);
  handler.trigger(100);
  
  // Get function pointer
  auto callback = getCallback(true);
  callback(50);
}

// Test inheritance and virtual calls
void testInheritance() {
  // Create derived object
  Derived derived;
  derived.virtualMethod();  // Virtual call
  derived.nonVirtualMethod();  // Non-virtual call
  derived.derivedMethod();  // Derived method
  
  // Polymorphic call through base pointer
  Base* basePtr = &derived;
  basePtr->virtualMethod();  // Virtual dispatch
  int result = basePtr->pureVirtualMethod();  // Pure virtual call
  
  // Multiple inheritance
  MultiDerived multi;
  multi.virtualMethod();  // From Base through Derived
  multi.interfaceMethod();  // From Interface
  multi.multiMethod();  // Own method
  
  // Interface pointer
  Interface* ifacePtr = &multi;
  ifacePtr->interfaceMethod();  // Virtual call through interface
}

// Test templates
void testTemplates() {
  // Template class instantiation
  Container<int> intContainer(42);
  Container<double> doubleContainer(3.14);
  Container<std::string> stringContainer("test");
  
  // Template function
  processValue(100);
  processValue(2.718);
  
  // Template processor
  Processor<int> intProc;
  int value = intProc.process(10);
  
  Processor<int*> ptrProc;
  int* ptr = &value;
  ptrProc.process(ptr);
}

// Test enums
void testEnums() {
  Color color = RED;
  Status status = Status::ACTIVE;
  
  switch (color) {
    case RED:
      break;
    case GREEN:
      break;
    case BLUE:
      break;
  }
  
  if (status == Status::ACTIVE) {
    status = Status::PENDING;
  }
}

// Test structs
void testStructs() {
  Point p1(3.0, 4.0);
  double dist = p1.distance();
  
  Point p2(1.0, 1.0);
  double dist2 = p2.distance();
}

// Test object creation
void testObjectCreation() {
  // Stack allocation
  Derived stackObj;
  
  // Heap allocation
  Derived* heapObj = new Derived();
  delete heapObj;
  
  // Smart pointer
  std::unique_ptr<Derived> smartPtr = std::make_unique<Derived>();
  
  // Array
  Derived* array = new Derived[5];
  delete[] array;
}

// Nested namespace
namespace Nested {
  void nestedFunction() {
    // Call function from parent namespace
    freeFunction(20);
  }
}

int main() {
  // Direct inter-file calls from main()
  // Call free functions from base.cpp
  freeFunction(5);
  int sum = calculateSum(10, 20);
  
  // Create objects from other files and call their methods
  Derived derivedObj;
  derivedObj.virtualMethod();
  derivedObj.derivedMethod();
  int value = derivedObj.pureVirtualMethod();
  
  // Polymorphic call through base pointer
  Base* basePtr = &derivedObj;
  basePtr->virtualMethod();
  
  // Call function pointer utilities from function_pointers.cpp
  executeCallback(callbackFunction, 100);
  auto callback = getCallback(true);
  callback(50);
  
  // Use callback handler from function_pointers.cpp
  CallbackHandler handler;
  handler.setCallback(anotherCallback);
  handler.trigger(200);
  
  // Test all features through helper functions
  testInterFileCalls();
  testInheritance();
  testTemplates();
  testEnums();
  testStructs();
  testObjectCreation();
  testOperators();
  TestNamespace::useStdFunction();
  TestNamespace::testFunctionParameter();
  
  // Nested namespace call
  Nested::nestedFunction();
  
  // Lambda with capture (C++11 feature)
  int captured = 42;
  auto lambda = [captured](int x) {
    return x + captured;
  };
  int lambdaResult = lambda(10);
  
  return 0;
}

// Made with Bob
