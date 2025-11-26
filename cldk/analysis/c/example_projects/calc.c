// C Program to make a Simple Calculator using
// switch-case statements
#include <stdio.h>
#include <float.h>

double add(double x, double y) {
  double res = x + y;
  return res;
}

double subtract(double x, double y) {
  double res = x - y;
  return res;
}

double multiply(double x, double y) {
  double res = x * y;
  return res;
}

double divide(double x, double y) {
  double res = x / y;
  return res;
}

double print_error() {
  printf("Error! Incorrect Operator Value\n");
  double res = -DBL_MAX;
  return res;
}

int main() {
    char op;
    double a, b, res;

    // Read the operator
    printf("Enter an operator (+, -, *, /): ");
    scanf("%c", &op);

    // Read the two numbers
    printf("Enter two operands: ");
    scanf("%lf %lf", &a, &b);

    // Define all four operations in the corresponding
    // switch-case
    switch (op) {
    case '+':
        res = add(a, b);
        break;
    case '-':
        res = subtract(a, b);
        break;
    case '*':
        res = multiply(a, b);
        break;
    case '/':
        res = divide(a, b);
        break;
    default:
        res = print_error();
    }
    if(res!=-DBL_MAX)
      printf("result: \n%.2lf\n\n", res);

    printf("GOODBYE\n");
    return 0;
}
