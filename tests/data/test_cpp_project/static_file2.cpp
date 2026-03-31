// Test case for static function handling with USR-based identification
// This file contains a static function with the SAME NAME as in static_file1.cpp

#include <iostream>

// Static function in this TU - same name but different USR
static void helper() {
  std::cout << "Helper from static_file2.cpp\n";
}

void callHelperFromFile2() {
  helper();  // Should link to THIS file's static helper via USR, not file1's
}

// Made with Bob
