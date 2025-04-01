import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KeypointContainerComponent } from './keypoint-container.component';

describe('KeypointContainerComponent', () => {
  let component: KeypointContainerComponent;
  let fixture: ComponentFixture<KeypointContainerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [KeypointContainerComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(KeypointContainerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
