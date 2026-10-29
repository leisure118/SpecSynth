int main()
{
	int x=0,y=50000,z=0;
	x=0;
	/*@
	  loop invariant 0 <= x <= 1000000;
	  loop invariant x <= 50000 ==> y == 50000;
	  loop invariant x >= 50000 ==> y == x;
	  loop assigns x, y;
	  loop variant 1000000 - x;
	*/
	while(x<1000000){
		if(x<50000)
			x++;
		else{
			x++;
			y++;
		}
	}
	/*@
	  loop invariant 0 <= y;
	  loop invariant x == y;
	  loop invariant y % 2 == 0;
	  loop assigns x, y;
	  loop variant y;
	*/
	while(y>0){
		y=y-2;
		x=x-2;
	}
	 //@ assert(z==x);
	return 0;
}
