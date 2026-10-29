#include<math.h>
/*@
  requires x >= 0.0;
  requires \is_finite(x);
  ensures \result == sqrt(x);
  assigns \nothing;
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