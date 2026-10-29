int main(){
	int x=0,y=50000,z=0;
	x=0;
	/*@
	  loop invariant 0 <= x <= 1000000;
	  loop invariant (x < 50000 ==> y == 50000) && (x >= 50000 ==> y == x);
	  loop invariant (x >= 50000 ==> x % 2 == 0);
	  loop assigns x, y;
	  loop variant 1000000 - x;
	*/
	while(x<1000000){
		if(x<50000)
			x++;
		else{
			x=x+2;
			y=y+2;
		}
	}
	/*@
	  loop invariant 0 <= y <= 1000000;
	  loop invariant x == y;
	  loop assigns x, y;
	  loop variant y;
	*/
	while(y>z){
		y--;
		x--;
	}
	//@assert((x%2==0));
	return 0;
}
