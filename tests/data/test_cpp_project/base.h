#pragma once
#include <string>

// Namespace for testing
namespace TestNamespace {

// Enum for testing
enum Color { RED, GREEN, BLUE };

// Enum class for testing
enum class Status { ACTIVE, INACTIVE, PENDING };

// Base class for inheritance testing
class Base {
 public:
  Base();
  virtual ~Base();
  virtual void virtualMethod();
  virtual int pureVirtualMethod() = 0;
  void nonVirtualMethod();

 protected:
  int baseValue;
};

// Struct for testing
struct Point {
  double x;
  double y;
  Point(double x, double y);
  double distance() const;
};

// Function pointer type
typedef void (*FunctionPointer)(int);

// Template class
template <typename T>
class Container {
 public:
  Container(T value) : data(value) {}
  T getData() const { return data; }
  void setData(T value) { data = value; }

 private:
  T data;
};

// Free function declarations
void freeFunction(int x);
int calculateSum(int a, int b);

}  // namespace TestNamespace

// Made with Bob
