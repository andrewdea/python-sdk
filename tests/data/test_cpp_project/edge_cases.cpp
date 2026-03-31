// Edge cases test file for comprehensive symbol extraction testing
#include "edge_cases.h"

namespace EdgeCases {

// ============================================================================
// Friend Declarations
// ============================================================================

class FriendTestClass {
 private:
  int private_data;
  friend class FriendAccessor;
  friend void friendFunction(FriendTestClass& obj);
};

class FriendAccessor {
 public:
  void accessPrivate(FriendTestClass& obj) { obj.private_data = 42; }
};

void friendFunction(FriendTestClass& obj) { obj.private_data = 100; }

// ============================================================================
// Using Declarations
// ============================================================================

namespace Inner {
void innerFunction() {}
class InnerClass {};
}  // namespace Inner

using Inner::innerFunction;
using Inner::InnerClass;

// ============================================================================
// Anonymous Namespace
// ============================================================================

namespace {
void anonymousFunction() {}
int anonymousVariable = 42;
}  // namespace

// ============================================================================
// Anonymous Union/Struct
// ============================================================================

struct ContainerWithAnonymous {
  union {
    int as_int;
    float as_float;
  };
  
  struct {
    int x;
    int y;
  };
};

// ============================================================================
// Nested Templates
// ============================================================================

template <typename T>
class OuterTemplate {
 public:
  template <typename U>
  class InnerTemplate {
   public:
    T outer_value;
    U inner_value;
    
    template <typename V>
    V nestedMethod(V val) {
      return val;
    }
  };
};

// Instantiation
OuterTemplate<int>::InnerTemplate<double> nestedInstance;

// ============================================================================
// Variadic Templates
// ============================================================================

template <typename... Args>
void variadicFunction(Args... args) {}

template <typename T, typename... Rest>
class VariadicClass {
 public:
  T first;
  VariadicClass<Rest...>* rest;
};

// Instantiations
void testVariadic() {
  variadicFunction(1, 2.0, "three");
  VariadicClass<int, double, char> varInstance;
}

// ============================================================================
// C++11/14/17/20 Attributes
// ============================================================================

[[nodiscard]] int attributedFunction() { return 42; }

[[deprecated("Use newFunction instead")]] void oldFunction() {}

class [[deprecated]] OldClass {};

struct AttributedStruct {
  [[maybe_unused]] int unused_field;
  [[nodiscard]] bool checkStatus() { return true; }
};

// ============================================================================
// Constexpr and Consteval (C++20)
// ============================================================================

constexpr int constexprFunction(int x) { return x * 2; }

#if __cplusplus >= 202002L
consteval int constevalFunction(int x) { return x * 3; }
#endif

// ============================================================================
// Concepts (C++20)
// ============================================================================

#if __cplusplus >= 202002L
// Concepts are already declared in header, just provide template implementations
template <Numeric T>
T add(T a, T b) {
  return a + b;
}
#endif

// ============================================================================
// Inline Namespace
// ============================================================================

inline namespace v1 {
void versionedFunction() {}
}  // namespace v1

namespace v2 {
void versionedFunction() {}
}  // namespace v2

// ============================================================================
// Static Local Variables
// ============================================================================

int functionWithStaticLocal() {
  static int counter = 0;
  return ++counter;
}

// ============================================================================
// Complex Template Specializations
// ============================================================================

template <typename T>
struct TemplateStruct {
  T value;
};

// Partial specialization for pointers
template <typename T>
struct TemplateStruct<T*> {
  T* ptr;
};

// Full specialization for int
template <>
struct TemplateStruct<int> {
  int special_value;
};

// ============================================================================
// SFINAE and Enable_if
// ============================================================================

template <typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
sfinaeFunction(T value) {
  return value * 2;
}

template <typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
sfinaeFunction(T value) {
  return value * 3.0;
}

// ============================================================================
// Conversion Operators
// ============================================================================

class ConversionClass {
 public:
  operator int() const { return 42; }
  operator bool() const { return true; }
  explicit operator double() const { return 3.14; }
};

// ============================================================================
// Deleted and Defaulted Functions
// ============================================================================

class SpecialMemberClass {
 public:
  SpecialMemberClass() = default;
  SpecialMemberClass(const SpecialMemberClass&) = delete;
  SpecialMemberClass(SpecialMemberClass&&) = default;
  SpecialMemberClass& operator=(const SpecialMemberClass&) = delete;
  SpecialMemberClass& operator=(SpecialMemberClass&&) = default;
  ~SpecialMemberClass() = default;
};

}  // namespace EdgeCases

// Made with Bob
