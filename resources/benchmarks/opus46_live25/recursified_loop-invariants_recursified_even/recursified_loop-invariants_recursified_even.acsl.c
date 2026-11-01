#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires \valid(x);
  requires *x % 2 == 0;
  assigns *x;
  ensures *x % 2 == 0;
*/
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      unsigned int prev = *x;
      *x += 2;
      //@ assert prev <= 4294967293 ==> *x == prev + 2;
      //@ assert prev == 4294967294 ==> *x == 0;
      //@ assert *x % 2 == 0;
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
  //@assert(!(x % 2));
  return 0;
}
