#pragma once

#include <type_traits>
#include <concepts>

namespace EdgeCases {

// Forward declarations
class FriendTestClass;
class FriendAccessor;
void friendFunction(FriendTestClass& obj);

// Using declarations
namespace Inner {
void innerFunction();
class InnerClass;
}  // namespace Inner

// Template declarations
template <typename T>
class OuterTemplate;

template <typename... Args>
void variadicFunction(Args... args);

template <typename T, typename... Rest>
class VariadicClass;

// Attributed functions
[[nodiscard]] int attributedFunction();
[[deprecated("Use newFunction instead")]] void oldFunction();

// Constexpr
constexpr int constexprFunction(int x);
inline constexpr int constexprVariable = 42;

#if __cplusplus >= 202002L
consteval int constevalFunction(int x);

// Concepts
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <Numeric T>
T add(T a, T b);

template <typename T>
concept Printable = requires(T t) {
  { t.print() };
};
#endif

// Inline namespace
inline namespace v1 {
void versionedFunction();
}

namespace v2 {
void versionedFunction();
}

// Template specializations
template <typename T>
struct TemplateStruct;

// SFINAE
template <typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
sfinaeFunction(T value);

template <typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
sfinaeFunction(T value);

// Conversion operators
class ConversionClass;

// Special member functions
class SpecialMemberClass;

}  // namespace EdgeCases

// Made with Bob
