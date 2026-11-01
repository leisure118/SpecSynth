int main()
{
  unsigned int x = 0;
  unsigned int y = 0;
  unsigned int z = 0;
  unsigned int w = 0;
  unsigned int v = 0;
  /*@
    loop invariant 0 <= w <= 0x0fffffff;
    loop assigns w, x, y, z, v;
    loop variant 0x0fffffff - w;
  */
  for(w=0;w<0x0fffffff;w++)
  	/*@
  	  loop invariant 0 <= x <= 10;
  	  loop assigns x, y, z, v;
  	  loop variant 10 - x;
  	*/
  	for(x=0;x< 10;x++)
	   /*@
	     loop invariant 0 <= y <= 10;
	     loop assigns y, z, v;
	     loop variant 10 - y;
	   */
	   for(y=0;y< 10;y++)
		/*@
		  loop invariant 0 <= z <= 10;
		  loop assigns z, v;
		  loop variant 10 - z;
		*/
		for(z=0;z< 10;z++) {
			/*@
			  loop invariant 0 <= v <= 10;
			  loop assigns v;
			  loop variant 10 - v;
			*/
			for(v=0;v< 10;v++);
			//@ assert(v % 4);
	   }
  return 0;
}
