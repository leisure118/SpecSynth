#include<math.h>
/*@
  requires \is_finite(x);
  requires x >= 0;
  assigns \nothing;
  ensures \result == sqrt(x);
*/
double Sqrt(double x){	
	return sqrt(x);
}
int main(){
	double x = 9;
	double y;
	y = Sqrt(x);
	//@assert y == sqrt(x); 
	return 0;
}