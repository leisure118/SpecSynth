/*@
  requires \valid(i) && \valid(j) && \valid(k);
  requires *k == 3 * *i && *j == 2 * *i;
  assigns *i, *j, *k;
  ensures *k == 3 * *i && *j == 2 * *i;
*/
void func_to_recursive_line_20_to_24_0(unsigned int *i, unsigned int *k, unsigned int *j)
{
  if ((*k) < 0x0fffffff)
  {
    {
      *i = (*i) + 1;
      *j = (*j) + 2;
      *k = (*k) + 3;
      //@ admit *k == 3 * *i;
      //@ admit *j == 2 * *i;
      //@assert(((*k) == (3 * (*i))) && ((*j) == (2 * (*i))));
    }
    func_to_recursive_line_20_to_24_0(i, k, j);
  }
  else
  {
  }
}
int main()
{
  unsigned int i = 0;
  unsigned int j = 0;
  unsigned int k = 0;
  func_to_recursive_line_20_to_24_0(&i, &k, &j);
  //@assert((k == (3 * i)) && (j == (2 * i)));
}
