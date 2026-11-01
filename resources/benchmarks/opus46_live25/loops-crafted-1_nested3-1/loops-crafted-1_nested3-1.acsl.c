int main()
{
  unsigned int x = 0;
  unsigned int y = 0;
  unsigned int z = 0;
  unsigned int w = 0;
  /*@
    loop invariant 0 <= x <= 268435455;
    loop assigns x, y, z;
    loop variant 268435455 - x;
  */
  while (x < 0x0fffffff) {
    y = 0;
    /*@
      loop invariant 0 <= y <= 268435455;
      loop assigns y, z;
      loop variant 268435455 - y;
    */
    while (y < 0x0fffffff) {
   	z =0;
	/*@
	  loop invariant 0 <= z <= 268435455;
	  loop assigns z;
	  loop variant 268435455 - z;
	*/
	while (z <0x0fffffff) {
	  z++;
	}
    	//@ assert(z % 4);
	y++;
    }
    //@ assert(y % 2);
    x++;
  }
  //@ assert(x % 2);
  return 0;
}
