SpriteTest.smc: memoryMap.cfg spriteTest.o
	ld65 -C memoryMap.cfg -o SpriteTest.smc spriteTest.o

spriteTest.o: spriteTest.asm mySprite.vra
	ca65 --cpu 65816 -s -o spriteTest.o spriteTest.asm

mySprite.vra: sprite_test.png
	python scrunch.py --sizeX 16 --sizeY 16 sprite_test.png

clean:
	rm SpriteTest.smc spriteTest.o mySprite.vra mySprite.pal tile*png