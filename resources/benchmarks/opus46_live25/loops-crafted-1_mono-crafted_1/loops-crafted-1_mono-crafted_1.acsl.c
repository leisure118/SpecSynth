int main()
{
	int x=0,y=50000,z=0;
	x=0;
	/*@
	  loop invariant 0 <= x <= 1000000;
	  loop invariant z == 0;
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
	  loop invariant x == y;
	  loop invariant z == 0;
	  loop invariant y >= z;
	  loop assigns x, y;
	  loop variant y - z;
	*/
	while(y>z){
		y--;
		x--;
	}
	//@ assert(x==z);
	return 0;
}
