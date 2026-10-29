void func_to_recursive_line_20_to_25_0(unsigned int *k, unsigned int *j, unsigned int *i)
{
  if ((*k) < 0x0fffffff)
  {
    {
      *i = (*i) + 1;
      *j = (*j) + 2;
      *k = (*k) + 3;
      //@assert((*k) == ((*i) + (*j)));
    }
    func_to_recursive_line_20_to_25_0(k, j, i);
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
  func_to_recursive_line_20_to_25_0(&k, &j, &i);
  //@assert(k == (i + j));
}
