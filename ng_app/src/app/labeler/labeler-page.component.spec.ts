import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LabelerPageComponent } from './labeler-page.component';

describe('LabelerPageComponent', () => {
  let component: LabelerPageComponent;
  let fixture: ComponentFixture<LabelerPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LabelerPageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LabelerPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
