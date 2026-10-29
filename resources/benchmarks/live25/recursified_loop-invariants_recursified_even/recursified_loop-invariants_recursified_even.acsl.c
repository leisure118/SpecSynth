#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires \valid(x);
  ensures *x % 2 == \old(*x) % 2;
  assigns *x;
*/
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      *x += 2;
    }
    func_to_recursive_line_13_to_14_0(x);
  }
  else
  {
  }
  //@ admit *x % 2 == \at(*x, Pre) % 2;
}
int main(void)
{
  unsigned int x = 0;
  func_to_recursive_line_13_to_14_0(&x);
  //@assert(!(x % 2));
  return 0;
}
