int main(){
	int x=0,y=500000,z=0;
	x=0;
	/*@
	  loop invariant 0 <= x <= 1000000;
	  loop invariant z == 0;
	  loop invariant x <= 500000 ==> y == 500000;
	  loop invariant x >= 500000 ==> y == x;
	  loop assigns x, y;
	  loop variant 1000000 - x;
	*/
	while(x<1000000){
		if(x<500000)
			x++;
		else{
			x++;
			y++;
		}
	}
	/*@
	  loop invariant x + z == 1000000;
	  loop invariant y + 2*z == 1000000;
	  loop invariant y >= 0;
	  loop assigns x, y, z;
	  loop variant y;
	*/
	while(y>0){
		x--;
		z++;
		y=y-2;
	}
	//@ assert(z%2==0);
	//@ assert(x%2==0);
	return 0;
}
