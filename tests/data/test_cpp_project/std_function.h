#pragma once
#include <functional>

namespace TestNamespace {

void targetFunction(int x);
void anotherTarget(int x);

void useStdFunction();
void passFunctionAsParameter(std::function<void(int)> callback);
void testFunctionParameter();

} // namespace TestNamespace

// Made with Bob
