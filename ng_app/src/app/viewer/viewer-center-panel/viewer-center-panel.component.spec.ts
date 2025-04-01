import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewerCenterPanelComponent } from './viewer-center-panel.component';

describe('ViewerCenterPanelComponent', () => {
  let component: ViewerCenterPanelComponent;
  let fixture: ComponentFixture<ViewerCenterPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewerCenterPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ViewerCenterPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
