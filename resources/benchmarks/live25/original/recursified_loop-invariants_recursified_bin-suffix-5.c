#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      *x += 8;
    }
    func_to_recursive_line_13_to_14_0(x);
  }
  else
  {
  }
}
int main(void)
{
  unsigned int x = 5;
  func_to_recursive_line_13_to_14_0(&x);
  //@assert((x & 5) == 5);
  return 0;
}
