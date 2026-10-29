#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires \valid(x);
  assigns *x;
  ensures \old(*x) % 4 == *x % 4;
*/
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      *x += 4;
      //@ admit *x % 4 == \at(*x, Pre) % 4;
    }
    func_to_recursive_line_13_to_14_0(x);
  }
  else
  {
  }
}
int main(void)
{
  unsigned int x = 0;
  func_to_recursive_line_13_to_14_0(&x);
  //@assert(!(x % 4));
  return 0;
}
