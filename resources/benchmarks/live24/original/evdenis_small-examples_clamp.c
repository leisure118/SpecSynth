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