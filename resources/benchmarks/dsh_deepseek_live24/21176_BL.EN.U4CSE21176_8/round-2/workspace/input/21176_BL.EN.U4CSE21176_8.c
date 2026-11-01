#include<math.h>
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