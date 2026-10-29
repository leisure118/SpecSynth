int unknown1();
int unknown2();
int unknown3();

void foo(int k)
{
  int z = k;
  int x = 0;
  int y = 0;

  /*@
    loop invariant x == y;
    loop invariant z == k + y;
    loop assigns x, y, z;
  */
  while(unknown1())
  {
    int c = 0;
    /*@
      loop invariant x == y;
      loop invariant z == k + y - c;
      loop assigns x, y, c;
    */
    while(unknown2())
    {
      if(z==k+y-c)
      {
        x++;
        y++;
        c++;
      }else
      {
        x++;
        y--;
        c++;
      }
    }
    /*@
      loop invariant x == y;
      loop assigns x, y;
    */
    while(unknown3())
    {
      x--;
      y--;
    }
    z=k+y;
  }
  //@ assert(x==y);
}
