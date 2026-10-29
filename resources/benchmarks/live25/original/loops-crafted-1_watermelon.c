#include<limits.h>
/*@
assigns \nothing;
ensures 0 < \result < 10000000;
*/
int unknown();
int true = 1;
int false = 0;
int correct_version(int w)
{
  int is_divisible = true;
  if(w < 4)
    is_divisible = false;
  else
  {
    int i;
    for(i = 0; i < w; i += 2)
    {}
    if(i != w)
      is_divisible = false;
  }
  return is_divisible;
}
int student_version(int w)
{
  int is_divisible = true;
  if(w < 4)
    is_divisible = false;
  else
  {
    int i;
    for(i = 0; i < w; i += 2)
    {}
    if(i != w)
      is_divisible = false;
  }
  return is_divisible;
}
int main(){
  int w=unknown();
  int is_divisible1 = true, is_divisible2 = true;
  if(w > 0 && w < 10000000)
  {
    is_divisible1 = correct_version(w);
    is_divisible2 = student_version(w);
    //@ assert(is_divisible1 == is_divisible2);
  }
  return 0;
}
