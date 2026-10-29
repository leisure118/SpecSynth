#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
void func_to_recursive_line_13_to_18_0(unsigned int *s)
{
  if (unknown())
  {
    {
      if ((*s) != 0)
      {
        ++(*s);
      }
      else
      {
      }
      if (unknown())
      {
        //@assert((*s) == 0);
      }
      else
      {
      }
    }
    func_to_recursive_line_13_to_18_0(s);
  }
  else
  {
  }
}
int main(void)
{
  unsigned int s = 0;
  func_to_recursive_line_13_to_18_0(&s);
  return 0;
}
