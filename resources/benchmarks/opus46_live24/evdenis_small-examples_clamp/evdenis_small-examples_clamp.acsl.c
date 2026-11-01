/*@
  assigns \nothing;
  ensures v > min ==> (v < max ==> \result == v);
  ensures v > min ==> (v >= max ==> \result == max);
  ensures v <= min ==> (min < max ==> \result == min);
  ensures v <= min ==> (min >= max ==> \result == max);
*/
int clamp(int v, int min, int max)
{
	int low = v > min ? v : min;
	return low < max ? low : max;
}
int main(){
	int a = 10;
	int b = 20;
	int c = clamp(a, b, 15);
	//@ assert c == 15;
}
